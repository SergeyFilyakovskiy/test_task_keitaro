import logging
import re
import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.campaign import CampaignCreateRequest
from app.core.config import settings
from app.infrastructure.db.repositories.campaign import CampaignRepository
from app.infrastructure.db.repositories.flow import FlowRepository
from app.infrastructure.db.repositories.flow_offer import FlowOfferRepository
from app.infrastructure.external.keitaro_client import KeitaroClient
from app.services import keitaro_consts as kc
from app.services.errors import EntityNotFoundError
from app.services.snapshots import build_snapshot, build_snapshot_from_rows

logger = logging.getLogger(__name__)


class CampaignService:
    def __init__(self, session: AsyncSession, client: KeitaroClient):
        self.session = session
        self.client = client
        self.campaign_repo = CampaignRepository(session)
        self.flow_repo = FlowRepository(session)
        self.offer_repo = FlowOfferRepository(session)

    # ---------- Часть 1: создаватор кампаний ----------

    async def create_campaign(self, data: CampaignCreateRequest):
        domain_id = await self._resolve_domain(data.domain_id)
        group_id = await self._resolve_group(
            data.group_name or settings.keitaro_default_group_name
        )
        source_id = await self._resolve_source(
            data.source_name or settings.keitaro_default_source_name
        )
        alias = self._generate_alias(data.name)

        kt_campaign = await self.client.create_campaign(
            {
                "name": data.name,
                "alias": alias,
                "domain_id": domain_id,
                "group_id": group_id,
                "traffic_source_id": source_id,
                "type": "position",
            }
        )
        campaign = await self.campaign_repo.create(
            keitaro_campaign_id=kt_campaign["id"],
            name=data.name,
            alias=alias,
            domain_id=domain_id,
            group_id=group_id,
            traffic_source_id=source_id,
        )

        # Flow 1: ловит указанных geo и редиректит на google
        kt_flow1 = await self.client.create_stream(
            {
                "campaign_id": kt_campaign["id"],
                "schema": kc.FLOW_SCHEMA_REDIRECT,
                "type": "forced",
                "name": kc.FLOW_GEO_NAME,
                "action_type": kc.FLOW_ACTION_REDIRECT,
                "action_payload": kc.REDIRECT_URL,
                "position": 1,
                "filters": [
                    {
                        "name": kc.COUNTRY_FILTER,
                        "mode": kc.COUNTRY_FILTER_MODE,
                        "payload": data.geo,
                    }
                ],
            }
        )
        await self.flow_repo.create(
            campaign_id=campaign.id,
            keitaro_flow_id=kt_flow1["id"],
            name=kc.FLOW_GEO_NAME,
            position=1,
            schema_type=kc.FLOW_SCHEMA_REDIRECT,
            action_type=kc.FLOW_ACTION_REDIRECT,
            action_payload=kc.REDIRECT_URL,
            filters={"country": data.geo},
            last_synced_snapshot={"offers": []},
        )

        # Flow 2: дефолтный, ротация на выбранный оффер (1 оффер = 100%)
        offer = await self.client.get_offer(data.offer_id)
        kt_flow2 = await self.client.create_stream(
            {
                "campaign_id": kt_campaign["id"],
                "schema": kc.FLOW_SCHEMA_OFFERS,
                "type": "default",
                "name": kc.FLOW_OFFERS_NAME,
                "action_type": kc.FLOW_ACTION_OFFERS,
                "position": 2,
                "offers": [{"offer_id": data.offer_id, "share": 100, "state": "active"}],
            }
        )
        flow2 = await self.flow_repo.create(
            campaign_id=campaign.id,
            keitaro_flow_id=kt_flow2["id"],
            name=kc.FLOW_OFFERS_NAME,
            position=2,
            schema_type=kc.FLOW_SCHEMA_OFFERS,
            action_type=kc.FLOW_ACTION_OFFERS,
        )
        offer_rows = await self.offer_repo.bulk_create(
            flow2.id,
            [
                {
                    "keitaro_offer_id": data.offer_id,
                    "offer_name": offer.get("name") or f"Offer {data.offer_id}",
                    "share": 100,
                    "pinned_share": None,
                    "is_active": True,
                    "is_deleted_in_keitaro": False,
                    "position": 0,
                }
            ],
        )

        flow2.last_synced_snapshot = build_snapshot_from_rows(offer_rows)
        await self.session.flush()

        logger.info("Campaign %s created (keitaro_id=%s)", campaign.id, campaign.keitaro_campaign_id)
        return await self.campaign_repo.get_by_id(campaign.id)

    # ---------- Чтение ----------

    async def list_campaigns(self):
        return await self.campaign_repo.list_all()

    async def get_campaign(self, campaign_id: int):
        campaign = await self.campaign_repo.get_by_id(campaign_id)
        if not campaign:
            raise EntityNotFoundError(f"Campaign {campaign_id} not found")
        return campaign

    # ---------- Хелперы резолва справочников ----------

    async def _resolve_domain(self, domain_id: int | None) -> int | None:
        if domain_id:
            return domain_id
        if settings.keitaro_default_domain_id:
            return settings.keitaro_default_domain_id
        domains = await self.client.list_domains()
        active = [d for d in domains if d.get("state") == "active"]
        return active[0]["id"] if active else None

    async def _resolve_group(self, name: str) -> int | None:
        groups = await self.client.list_groups("campaigns")
        for g in groups:
            if g.get("name") == name:
                return g["id"]
        created = await self.client.create_group(name, "campaigns")
        return created["id"]

    async def _resolve_source(self, name: str) -> int | None:
        sources = await self.client.list_traffic_sources()
        for s in sources:
            if s.get("name") == name:
                return s["id"]
        created = await self.client.create_traffic_source(name)
        return created["id"]

    @staticmethod
    def _generate_alias(name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "campaign"
        return f"{slug}-{secrets.token_hex(3)}"
    