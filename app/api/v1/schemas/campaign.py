from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.schemas.flow import FlowOut


class CampaignCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, examples=["campaign 2"])
    geo: list[str] = Field(
        ..., min_length=1, description="Гео-коды стран", examples=[["AU"]]
    )
    offer_id: int = Field(..., description="ID оффера Keitaro для второго потока")
    domain_id: int | None = Field(None, description="По умолчанию — из конфига")
    group_name: str | None = Field(None, description="Создаётся, если нет в Keitaro")
    source_name: str | None = Field(None, description="Создаётся, если нет в Keitaro")


class CampaignListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keitaro_campaign_id: int
    name: str
    alias: str
    is_dirty: bool
    created_at: datetime


class CampaignDetails(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keitaro_campaign_id: int
    name: str
    alias: str
    domain_id: int | None
    group_id: int | None
    traffic_source_id: int | None
    flows: list[FlowOut]
    created_at: datetime

    @classmethod
    def from_orm_campaign(cls, campaign) -> CampaignDetails:
        return cls(
            id=campaign.id,
            keitaro_campaign_id=campaign.keitaro_campaign_id,
            name=campaign.name,
            alias=campaign.alias,
            domain_id=campaign.domain_id,
            group_id=campaign.group_id,
            traffic_source_id=campaign.traffic_source_id,
            flows=[FlowOut.from_orm_flow(f) for f in campaign.flows],
            created_at=campaign.created_at,
        )