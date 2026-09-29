from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("keitaro_campaign_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("alias", sa.String(length=255), nullable=False),
        sa.Column("domain_id", sa.Integer(), nullable=True),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column("traffic_source_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("keitaro_campaign_id"),
    )
    op.create_index(
        op.f("ix_campaigns_keitaro_campaign_id"),
        "campaigns",
        ["keitaro_campaign_id"],
        unique=True,
    )

    op.create_table(
        "flows",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("keitaro_flow_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("schema_type", sa.String(length=50), nullable=False),
        sa.Column("action_type", sa.String(length=50), nullable=False),
        sa.Column("action_payload", sa.JSON(), nullable=True),
        sa.Column("filters", sa.JSON(), nullable=True),
        sa.Column("last_synced_snapshot", sa.JSON(), nullable=True),
        sa.Column("is_synced", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_flows_campaign_id"), "flows", ["campaign_id"], unique=False)
    op.create_index(
        op.f("ix_flows_keitaro_flow_id"), "flows", ["keitaro_flow_id"], unique=False
    )

    op.create_table(
        "flow_offers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("flow_id", sa.Integer(), nullable=False),
        sa.Column("keitaro_offer_id", sa.Integer(), nullable=False),
        sa.Column("offer_name", sa.String(length=255), nullable=False),
        sa.Column("share", sa.Integer(), nullable=False),
        sa.Column("pinned_share", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_deleted_in_keitaro", sa.Boolean(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["flow_id"], ["flows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_flow_offers_flow_id"), "flow_offers", ["flow_id"], unique=False
    )
    op.create_index(
        op.f("ix_flow_offers_keitaro_offer_id"),
        "flow_offers",
        ["keitaro_offer_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_flow_offers_keitaro_offer_id"), table_name="flow_offers")
    op.drop_index(op.f("ix_flow_offers_flow_id"), table_name="flow_offers")
    op.drop_table("flow_offers")
    op.drop_index(op.f("ix_flows_keitaro_flow_id"), table_name="flows")
    op.drop_index(op.f("ix_flows_campaign_id"), table_name="flows")
    op.drop_table("flows")
    op.drop_index(op.f("ix_campaigns_keitaro_campaign_id"), table_name="campaigns")
    op.drop_table("campaigns")
