from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(AsyncAttrs, DeclarativeBase):
   
    """

    Базовый класс от которого наследуются все
    модели таблиц БД

    """
    __abstract__ = True 

class Campaign(Base):

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True
        )
    
    keitaro_campaign_id: Mapped[int] = mapped_column(
        Integer, 
        unique=True, 
        nullable=False, 
        index=True
        )
    
    name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
        )
    
    alias: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
        )
    
    domain_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True
        )
    
    group_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True
        )
    
    traffic_source_id: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True
        )

    flows: Mapped[list["Flow"]] = relationship(
        "Flow",
        back_populates="campaign",
        cascade="all, delete-orphan",
        order_by="Flow.position",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name={self.name!r})>"

    @property
    def is_dirty(self) -> bool:
        return any(not flow.is_synced for flow in self.flows)


class Flow(Base):
    __tablename__ = "flows"

    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True
        )
    
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )

    keitaro_flow_id: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        index=True
        )
    
    name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
        )
    
    position: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0
        )
    
    schema_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False
        )  # landings|redirect|action
    
    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
        )  # ключ из /streams_actions
    
    action_payload: Mapped[Optional[dict | str]] = mapped_column(
        JSON,
        nullable=True
        )
    
    filters: Mapped[Optional[dict]] = mapped_column(
        JSON, 
        nullable=True
        )  # снапшот фильтров из Keitaro

    last_synced_snapshot: Mapped[Optional[dict]] = mapped_column(
        JSON, 
        nullable=True
        )

    is_synced: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=True
        )

    offers: Mapped[list["FlowOffer"]] = relationship(
        "FlowOffer",
        back_populates="flow",
        cascade="all, delete-orphan",
        order_by="FlowOffer.position",
    )

    campaign: Mapped["Campaign"] = relationship(
        "Campaign", 
        back_populates="flows"
        )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )


class FlowOffer(Base):

    __tablename__ = "flow_offers"

    id: Mapped[int] = mapped_column(
        Integer, 
        primary_key=True, 
        autoincrement=True
        )
    
    flow_id: Mapped[int] = mapped_column(
        ForeignKey("flows.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )

    keitaro_offer_id: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        index=True
        )
    
    offer_name: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
        )
    
    share: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0
        )  # текущий вес (int %)
    
    pinned_share: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True
        )  # если запинен — фиксируем
    
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=True
    )  # False = локально удален, доступен через bring back

    is_deleted_in_keitaro: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False
    )  # True = серый, удален в Keitaro

    position: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0
        )  # для порядка пересчета

    flow: Mapped["Flow"] = relationship(
        "Flow", 
        back_populates="offers"
        )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )
