from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.infrastructure.db.models import Flow


class FlowOfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keitaro_offer_id: int
    offer_name: str
    share: int
    pinned_share: int | None
    is_active: bool
    is_deleted_in_keitaro: bool
    position: int


class FlowOut(BaseModel):
    id: int
    keitaro_flow_id: int
    name: str
    position: int
    has_offers: bool
    is_synced: bool

    schema_type: str | None = None
    action_type: str | None = None
    action_payload: dict | str | None = None
    filters: dict | None = None
    offers: list[FlowOfferOut] = []

    @classmethod
    def from_orm_flow(cls, flow: Flow) -> FlowOut:
        
        has_offers = flow.schema_type == "landings" or bool(flow.offers)
        if not has_offers:
            return cls(
                id=flow.id,
                keitaro_flow_id=flow.keitaro_flow_id,
                name=flow.name,
                position=flow.position,
                has_offers=False,
                is_synced=flow.is_synced,
            )
        return cls(
            id=flow.id,
            keitaro_flow_id=flow.keitaro_flow_id,
            name=flow.name,
            position=flow.position,
            has_offers=True,
            is_synced=flow.is_synced,
            schema_type=flow.schema_type,
            action_type=flow.action_type,
            action_payload=flow.action_payload,
            filters=flow.filters,
            offers=[FlowOfferOut.model_validate(o) for o in flow.offers],
        )
    