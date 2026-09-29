from fastapi import APIRouter, Depends

from app.api.v1.schemas import OfferSearchItem
from app.core.dependencies import get_keitaro
from app.infrastructure.external.keitaro_client import KeitaroClient
from app.services.offer_service import OfferService

router = APIRouter()


@router.get("/offers/search", response_model=list[OfferSearchItem])
async def search_offers(
    q: str = "",
    limit: int = 20,
    client: KeitaroClient = Depends(get_keitaro),
):
    """Автокомплит офферов: прокси в Keitaro GET /offers."""
    return await OfferService(client).search(q, limit)