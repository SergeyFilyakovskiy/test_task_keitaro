import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models import FlowOffer
from app.infrastructure.db.repositories.campaign import CampaignRepository
from app.infrastructure.db.repositories.flow import FlowRepository
from app.infrastructure.db.repositories.flow_offer import FlowOfferRepository
from app.infrastructure.external.exceptions import KeitaroAPIError, KeitaroNotFoundError
from app.infrastructure.external.keitaro_client import KeitaroClient
from app.services import keitaro_consts as kc
from app.services.errors import (
    DomainValidationError,
    EntityNotFoundError,
    FlowDirtyError,
)
from app.services.snapshots import build_snapshot, build_snapshot_from_rows
from app.services.weight_service import OfferWeight, WeightService

logger = logging.getLogger(__name__)


class FlowService:
    def __init__(self, session: AsyncSession, client: KeitaroClient):
        self.session = session
        self.client = client
        self.campaign_repo = CampaignRepository(session)
        self.flow_repo = FlowRepository(session)
        self.offer_repo = FlowOfferRepository(session)

    # ---------- Fetch streams from KT ----------

    async def fetch_streams(self, campaign_id: int):
        campaign = await self.campaign_repo.get_by_id(campaign_id)
        if not campaign:
            raise EntityNotFoundError(f"Campaign {campaign_id} not found")
        if any(not f.is_synced for f in campaign.flows):
            raise FlowDirtyError(
                "Есть незапушенные изменения: запушь (push) или откати (cancel) их перед fetch"
            )

        kt_streams = await self.client.list_campaign_streams(campaign.keitaro_campaign_id)
        kt_by_id = {s["id"]: s for s in kt_streams}

        # Удалённые в KT потоки убираем из нашей БД
        for flow in list(campaign.flows):
            if flow.keitaro_flow_id not in kt_by_id:
                await self.flow_repo.delete(flow.id)

        existing = {
            f.keitaro_flow_id: f
            for f in campaign.flows
            if f.keitaro_flow_id in kt_by_id
        }

        for kt_stream in sorted(kt_streams, key=lambda s: s.get("position") or 0):
            flow = existing.get(kt_stream["id"])
            if flow is None:
                flow = await self.flow_repo.create(
                    campaign_id=campaign.id,
                    keitaro_flow_id=kt_stream["id"],
                    name=kt_stream.get("name") or f"Stream {kt_stream['id']}",
                    position=kt_stream.get("position") or 0,
                    schema_type=kt_stream.get("schema") or "",
                    action_type=kt_stream.get("action_type") or "",
                    action_payload=kt_stream.get("action_payload"),
                )
            else:
                flow.name = kt_stream.get("name") or flow.name
                flow.position = kt_stream.get("position") or flow.position
                flow.schema_type = kt_stream.get("schema") or flow.schema_type
                flow.action_type = kt_stream.get("action_type") or flow.action_type
                flow.action_payload = kt_stream.get("action_payload")

            await self.session.refresh(flow, ["offers"])
            if flow.schema_type == kc.FLOW_SCHEMA_OFFERS or kt_stream.get("offers"):
                await self._sync_offers_from_keitaro(flow, kt_stream.get("offers") or [])

            flow.is_synced = True
            await self.session.flush()
            await self.session.refresh(flow, ["offers"])
            flow.last_synced_snapshot = build_snapshot(flow)

        await self.session.flush()
        return await self.campaign_repo.get_by_id(campaign_id)

    async def _sync_offers_from_keitaro(self, flow, kt_offers: list[dict]) -> None:
        """
        Синк офферов из KT. Веса берём КАК ПРИШЛИ из KT — без пересчёта
        (если в KT удалили оффер, остальные сохраняют свои веса).
        """
        current = {o.keitaro_offer_id: o for o in flow.offers}
        seen: set[int] = set()

        for idx, kt_offer in enumerate(kt_offers):
            offer_id = kt_offer["offer_id"]
            seen.add(offer_id)
            row = current.get(offer_id)
            if row is None:
                name = await self._offer_name(offer_id)
                await self.offer_repo.bulk_create(
                    flow.id,
                    [
                        {
                            "keitaro_offer_id": offer_id,
                            "offer_name": name,
                            "share": kt_offer.get("share") or 0,
                            "pinned_share": None,
                            "is_active": True,
                            "is_deleted_in_keitaro": False,
                            "position": idx,
                        }
                    ],
                )
            else:
                row.share = kt_offer.get("share") or 0
                row.is_active = True
                row.is_deleted_in_keitaro = False
                row.position = idx

        # В KT оффера больше нет -> серый с кнопкой bring back, вес сохраняем
        for offer_id, row in current.items():
            if offer_id not in seen:
                row.is_active = False
                row.is_deleted_in_keitaro = True

    # ---------- Push to KT ----------

    async def push_flow(self, flow_id: int):
        flow = await self.flow_repo.get_by_id(flow_id)
        if not flow:
            raise EntityNotFoundError(f"Flow {flow_id} not found")

        active = [o for o in flow.offers if o.is_active]
        if not active:
            raise DomainValidationError("В потоке должен остаться минимум один активный оффер")

        await self.client.update_stream(
            flow.keitaro_flow_id,
            {
                "offers": [
                    {"offer_id": o.keitaro_offer_id, "share": o.share, "state": "active"}
                    for o in active
                ]
            },
        )
        for offer in flow.offers:
            offer.is_deleted_in_keitaro = not offer.is_active
        flow.is_synced = True
        await self.session.flush()
        await self.session.refresh(flow, ["offers"])
        flow.last_synced_snapshot = build_snapshot(flow)
        await self.session.flush()
        return flow

    # ---------- Cancel (откат к снапшоту) ----------

    async def cancel_flow(self, flow_id: int):
        flow = await self.flow_repo.get_by_id(flow_id)
        if not flow:
            raise EntityNotFoundError(f"Flow {flow_id} not found")

        snapshot = (flow.last_synced_snapshot or {}).get("offers", [])
        await self.offer_repo.delete_by_flow(flow.id)
        
        new_rows: list[FlowOffer] = []
        if snapshot:
            new_rows = await self.offer_repo.bulk_create(flow.id, snapshot)
        
        flow.is_synced = True
        await self.session.flush()
        
        flow.last_synced_snapshot = build_snapshot_from_rows(new_rows) if new_rows else {"offers": []}
        await self.session.flush()
        return flow

    # ---------- Мутации офферов (локальные, до push) ----------

    async def add_offer(self, flow_id: int, offer_id: int):
        def mutate(weights: list[OfferWeight]) -> None:
            existing = {w.offer_id for w in weights}
            if offer_id in existing:
                raise DomainValidationError(
                    "Оффер уже есть в потоке (для восстановления используй bring back)"
                )
            weights.append(OfferWeight(offer_id=offer_id, is_active=True))

        return await self._mutate_offers(flow_id, mutate, new_offer_id=offer_id)

    async def remove_offer(self, flow_id: int, offer_id: int):
        def mutate(weights: list[OfferWeight]) -> None:
            active_count = sum(1 for w in weights if w.is_active)
            target = next((w for w in weights if w.offer_id == offer_id), None)
            if target is None or not target.is_active:
                raise DomainValidationError(f"Offer {offer_id} not active in flow")
            if active_count <= 1:
                raise DomainValidationError("Нельзя удалить последний активный оффер")
            target.is_active = False

        return await self._mutate_offers(flow_id, mutate)

    async def bring_back_offer(self, flow_id: int, offer_id: int):
        def mutate(weights: list[OfferWeight]) -> None:
            target = next((w for w in weights if w.offer_id == offer_id), None)
            if target is None:
                raise DomainValidationError(f"Offer {offer_id} not found in flow history")
            target.is_active = True

        return await self._mutate_offers(flow_id, mutate)

    async def pin_offer(self, flow_id: int, offer_id: int, share: int):
        def mutate(weights: list[OfferWeight]) -> None:
            target = next(
                (w for w in weights if w.offer_id == offer_id and w.is_active), None
            )
            if target is None:
                raise DomainValidationError(f"Offer {offer_id} not active in flow")
            target.pinned_share = share

        return await self._mutate_offers(flow_id, mutate)

    async def unpin_offer(self, flow_id: int, offer_id: int):
        def mutate(weights: list[OfferWeight]) -> None:
            target = next((w for w in weights if w.offer_id == offer_id), None)
            if target is None:
                raise DomainValidationError(f"Offer {offer_id} not found in flow")
            target.pinned_share = None

        return await self._mutate_offers(flow_id, mutate)

    # ---------- Ядро мутаций ----------

    async def _mutate_offers(self, flow_id: int, mutate, new_offer_id: int | None = None):
        flow = await self.flow_repo.get_by_id(flow_id)
        if not flow:
            raise EntityNotFoundError(f"Flow {flow_id} not found")
        if flow.schema_type != kc.FLOW_SCHEMA_OFFERS and not flow.offers:
            raise DomainValidationError("Поток без офферов нельзя редактировать")

        rows = sorted(flow.offers, key=lambda o: o.position)
        weights = [
            OfferWeight(
                offer_id=o.keitaro_offer_id,
                is_active=o.is_active,
                pinned_share=o.pinned_share,
                share=o.share,
            )
            for o in rows
        ]

        mutate(weights)
        WeightService.recalculate_weights(weights)
        is_valid, error = WeightService.validate_weights(weights)
        if not is_valid:
            raise DomainValidationError(error)

        rows_by_id = {o.keitaro_offer_id: o for o in rows}
        for position, w in enumerate(weights):
            row = rows_by_id.get(w.offer_id)
            if row is None:
                name = await self._offer_name(w.offer_id)
                await self.offer_repo.bulk_create(
                    flow.id,
                    [
                        {
                            "keitaro_offer_id": w.offer_id,
                            "offer_name": name,
                            "share": w.share,
                            "pinned_share": w.pinned_share,
                            "is_active": w.is_active,
                            "is_deleted_in_keitaro": False,
                            "position": position,
                        }
                    ],
                )
            else:
                row.share = w.share
                row.pinned_share = w.pinned_share
                row.is_active = w.is_active
                row.position = position
                # bring back снимает "серость" локально; в KT оффер вернётся после push
                if w.is_active:
                    row.is_deleted_in_keitaro = False

        flow.is_synced = False  
        await self.session.flush()
        return await self.flow_repo.get_by_id(flow_id)

    # ---------- Хелперы ----------

    async def _offer_name(self, offer_id: int) -> str:
        try:
            offer = await self.client.get_offer(offer_id)
            return offer.get("name") or f"Offer {offer_id}"
        except KeitaroNotFoundError:
            return f"Offer {offer_id} (deleted)"
        except KeitaroAPIError:
            return f"Offer {offer_id}"