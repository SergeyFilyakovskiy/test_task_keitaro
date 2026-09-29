from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import AddOfferRequest, FlowOut, PinOfferRequest
from app.core.dependencies import get_db_session, get_keitaro
from app.infrastructure.external.keitaro_client import KeitaroClient
from app.services.flow_service import FlowService

router = APIRouter()


def _flow_out(flow) -> FlowOut:
    return FlowOut.from_orm_flow(flow)


@router.post("/flows/{flow_id}/push", response_model=FlowOut)
async def push_flow(
    flow_id: int,
    session: AsyncSession = Depends(get_db_session),
    client: KeitaroClient = Depends(get_keitaro),
):
    """Push to KT: применить локальные изменения потока в Keitaro."""
    flow = await FlowService(session, client).push_flow(flow_id)
    return _flow_out(flow)


@router.post("/flows/{flow_id}/cancel", response_model=FlowOut)
async def cancel_flow(
    flow_id: int,
    session: AsyncSession = Depends(get_db_session),
    client: KeitaroClient = Depends(get_keitaro),
):
    """Откат локальных изменений потока к последнему синку."""
    flow = await FlowService(session, client).cancel_flow(flow_id)
    return _flow_out(flow)


@router.post("/flows/{flow_id}/offers", response_model=FlowOut)
async def add_offer(
    flow_id: int,
    payload: AddOfferRequest,
    session: AsyncSession = Depends(get_db_session),
    client: KeitaroClient = Depends(get_keitaro),
):
    flow = await FlowService(session, client).add_offer(flow_id, payload.offer_id)
    return _flow_out(flow)


@router.delete("/flows/{flow_id}/offers/{offer_id}", response_model=FlowOut)
async def remove_offer(
    flow_id: int,
    offer_id: int,
    session: AsyncSession = Depends(get_db_session),
    client: KeitaroClient = Depends(get_keitaro),
):
    flow = await FlowService(session, client).remove_offer(flow_id, offer_id)
    return _flow_out(flow)


@router.post("/flows/{flow_id}/offers/{offer_id}/bring_back", response_model=FlowOut)
async def bring_back_offer(
    flow_id: int,
    offer_id: int,
    session: AsyncSession = Depends(get_db_session),
    client: KeitaroClient = Depends(get_keitaro),
):
    flow = await FlowService(session, client).bring_back_offer(flow_id, offer_id)
    return _flow_out(flow)


@router.put("/flows/{flow_id}/offers/{offer_id}/pin", response_model=FlowOut)
async def pin_offer(
    flow_id: int,
    offer_id: int,
    payload: PinOfferRequest,
    session: AsyncSession = Depends(get_db_session),
    client: KeitaroClient = Depends(get_keitaro),
):
    flow = await FlowService(session, client).pin_offer(flow_id, offer_id, payload.share)
    return _flow_out(flow)


@router.delete("/flows/{flow_id}/offers/{offer_id}/pin", response_model=FlowOut)
async def unpin_offer(
    flow_id: int,
    offer_id: int,
    session: AsyncSession = Depends(get_db_session),
    client: KeitaroClient = Depends(get_keitaro),
):
    flow = await FlowService(session, client).unpin_offer(flow_id, offer_id)
    return _flow_out(flow)