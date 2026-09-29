import sqlalchemy as sa
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models import Flow
from app.infrastructure.db.repositories.base import BaseRepository


class FlowRepository(BaseRepository):
    async def create(
        self,
        *,
        campaign_id: int,
        keitaro_flow_id: int,
        name: str,
        position: int,
        schema_type: str,
        action_type: str,
        action_payload: dict | str | None = None,
        filters: dict | None = None,
        last_synced_snapshot: dict | None = None,
        is_synced: bool = True,
    ) -> Flow:
        
        flow = Flow(
            campaign_id=campaign_id,
            keitaro_flow_id=keitaro_flow_id,
            name=name,
            position=position,
            schema_type=schema_type,
            action_type=action_type,
            action_payload=action_payload,
            filters=filters,
            last_synced_snapshot=last_synced_snapshot,
            is_synced=is_synced,
        )
        self.session.add(flow)
        await self.session.flush()
        return flow

    async def get_by_id(self, flow_id: int) -> Flow | None:
        stmt = (
            sa.select(Flow)
            .where(Flow.id == flow_id)
            .options(selectinload(Flow.offers))
        )
        return (await self.session.scalars(stmt)).unique().one_or_none()

    async def delete(self, flow_id: int) -> None:
        flow = await self.get_by_id(flow_id)
        if flow:
            await self.session.delete(flow)
            await self.session.flush()