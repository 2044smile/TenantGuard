"""initial_tables

Revision ID: 3d9bbaa402ba
Revises:
Create Date: 2026-04-26
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "3d9bbaa402ba"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── applications ──────────────────────────────────────────────────────────
    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", sa.String(64), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "collecting", "analyzing", "ready",
                "filling", "preview", "submitted", "failed",
                name="applicationstatus",
            ),
            nullable=True,
        ),
        # 임차인
        sa.Column("tenant_name", sa.String(50), nullable=True),
        sa.Column("tenant_resident_number_masked", sa.String(20), nullable=True),
        sa.Column("tenant_address", sa.String(200), nullable=True),
        sa.Column("tenant_phone", sa.String(20), nullable=True),
        # 임대인
        sa.Column("landlord_name", sa.String(100), nullable=True),
        sa.Column("landlord_address", sa.String(200), nullable=True),
        sa.Column("landlord_corp_number", sa.String(20), nullable=True),
        sa.Column("is_corporate_landlord", sa.Boolean(), nullable=True),
        # 부동산
        sa.Column("property_address", sa.String(200), nullable=True),
        sa.Column("property_area", sa.String(50), nullable=True),
        sa.Column("property_floor", sa.String(20), nullable=True),
        sa.Column("property_type", sa.String(50), nullable=True),
        # 계약
        sa.Column("contract_date", sa.DateTime(), nullable=True),
        sa.Column("deposit_amount", sa.BigInteger(), nullable=True),
        sa.Column("confirmed_date", sa.DateTime(), nullable=True),
        sa.Column("move_in_date", sa.DateTime(), nullable=True),
        # 결과
        sa.Column("ecourt_receipt_number", sa.String(50), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("extra_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        # 타임스탬프
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_applications_session_id", "applications", ["session_id"])
    op.create_index("ix_applications_status", "applications", ["status"])
    op.create_index("ix_applications_created_at", "applications", ["created_at"])

    # ── document_records ──────────────────────────────────────────────────────
    op.create_table(
        "document_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "doc_type",
            sa.Enum(
                "building_registry", "resident_registration", "lease_contract",
                "termination_notice", "corporate_registry", "building_ledger", "floor_plan",
                name="documenttype",
            ),
            nullable=False,
        ),
        sa.Column("storage_key", sa.String(500), nullable=True),
        sa.Column("is_auto_collected", sa.Boolean(), nullable=True),
        sa.Column("collected_at", sa.DateTime(), nullable=True),
        sa.Column("parsed_data", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=True),
        sa.Column("validation_errors", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_document_records_application_id",
        "document_records",
        ["application_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_document_records_application_id", table_name="document_records")
    op.drop_table("document_records")
    op.drop_index("ix_applications_created_at", table_name="applications")
    op.drop_index("ix_applications_status", table_name="applications")
    op.drop_index("ix_applications_session_id", table_name="applications")
    op.drop_table("applications")
    op.execute("DROP TYPE IF EXISTS applicationstatus")
    op.execute("DROP TYPE IF EXISTS documenttype")
