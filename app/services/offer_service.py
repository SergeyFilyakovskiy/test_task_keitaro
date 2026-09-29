from app.infrastructure.external.keitaro_client import KeitaroClient


class OfferService:
    """Прокси-поиск по офферам Keitaro для автокомплита."""

    def __init__(self, client: KeitaroClient):
        self.client = client

    async def search(self, query: str, limit: int = 20) -> list[dict]:
        offers = await self.client.list_offers()
        q = query.strip().lower()
        result = []
        for offer in offers:
            if offer.get("state") != "active":
                continue
            if not q or q in str(offer.get("name", "")).lower() or q == str(offer.get("id")):
                result.append({"id": offer["id"], "name": offer.get("name", "")})
            if len(result) >= limit:
                break
        return result