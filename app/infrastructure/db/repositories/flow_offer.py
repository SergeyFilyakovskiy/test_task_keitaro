import sqlalchemy as sa

from app.infrastructure.db.models import FlowOffer
from app.infrastructure.db.repositories.base import BaseRepository


class FlowOfferRepository(BaseRepository):

    async def bulk_create(self, flow_id: int, items: list[dict]) -> list[FlowOffer]:
        offers = [FlowOffer(flow_id=flow_id, **item) for item in items]
        self.session.add_all(offers)
        await self.session.flush()
        return offers

    async def delete_by_flow(self, flow_id: int) -> None:
        stmt = sa.delete(FlowOffer).where(FlowOffer.flow_id == flow_id)
        await self.session.execute(stmt)
        await self.session.flush()