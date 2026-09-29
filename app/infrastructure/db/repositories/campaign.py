import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import Campaign, Flow
from app.infrastructure.db.repositories.base import BaseRepository


class CampaignRepository(BaseRepository):
    _full_load = (selectinload(Campaign.flows).selectinload(Flow.offers),)

    async def create(
        self,
        *,
        keitaro_campaign_id: int,
        name: str,
        alias: str,
        domain_id: int | None = None,
        group_id: int | None = None,
        traffic_source_id: int | None = None,
    ) -> Campaign:
        campaign = Campaign(
            keitaro_campaign_id=keitaro_campaign_id,
            name=name,
            alias=alias,
            domain_id=domain_id,
            group_id=group_id,
            traffic_source_id=traffic_source_id,
        )
        self.session.add(campaign)
        await self.session.flush()
        return campaign

    async def get_by_id(self, campaign_id: int) -> Campaign | None:
        stmt = (
            sa.select(Campaign)
            .where(Campaign.id == campaign_id)
            .options(*self._full_load)
        )
        return (await self.session.scalars(stmt)).unique().one_or_none()

    async def list_all(self) -> list[Campaign]:
        stmt = (
            sa.select(Campaign)
            .options(selectinload(Campaign.flows))
            .order_by(Campaign.id)
        )
        return list((await self.session.scalars(stmt)).unique().all())