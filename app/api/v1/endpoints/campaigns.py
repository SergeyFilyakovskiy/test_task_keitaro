from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import (
    CampaignCreateRequest,
    CampaignDetails,
    CampaignListItem,
)
from app.core.dependencies import get_db_session, get_keitaro
from app.infrastructure.external.keitaro_client import KeitaroClient
from app.services.campaign_service import CampaignService
from app.services.flow_service import FlowService

router = APIRouter()


@router.post("/campaigns", response_model=CampaignDetails, status_code=201)
async def create_campaign(
    payload: CampaignCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    client: KeitaroClient = Depends(get_keitaro),
):
    """Часть 1: создаватор кампаний (name + geo + offer_id)."""
    service = CampaignService(session, client)
    campaign = await service.create_campaign(payload)
    return CampaignDetails.from_orm_campaign(campaign)


@router.get("/campaigns", response_model=list[CampaignListItem])
async def list_campaigns(
    session: AsyncSession = Depends(get_db_session),
):
    campaigns = await CampaignService(session, KeitaroClient()).list_campaigns()
    return [CampaignListItem.model_validate(c) for c in campaigns]


@router.get("/campaigns/{campaign_id}", response_model=CampaignDetails)
async def get_campaign(
    campaign_id: int,
    session: AsyncSession = Depends(get_db_session),
):
    campaign = await CampaignService(session, KeitaroClient()).get_campaign(campaign_id)
    return CampaignDetails.from_orm_campaign(campaign)


@router.post("/campaigns/{campaign_id}/fetch", response_model=CampaignDetails)
async def fetch_streams(
    campaign_id: int,
    session: AsyncSession = Depends(get_db_session),
    client: KeitaroClient = Depends(get_keitaro),
):
    """Fetch streams from KT. 409, если есть незапушенные изменения."""
    campaign = await FlowService(session, client).fetch_streams(campaign_id)
    return CampaignDetails.from_orm_campaign(campaign)