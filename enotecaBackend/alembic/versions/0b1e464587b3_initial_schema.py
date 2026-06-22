"""initial schema

Revision ID: 0b1e464587b3
Revises:
Create Date: 2026-06-22 11:55:46.626827

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import CHAR


# revision identifiers, used by Alembic.
revision: str = '0b1e464587b3'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vini",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("produttore", sa.String(255), nullable=False),
        sa.Column("annata", sa.Integer(), nullable=True),
        sa.Column("azienda_vinicola", sa.String(255), nullable=False),
        sa.Column("denominazione", sa.String(100), nullable=True),
        sa.Column("regione", sa.String(100), nullable=False),
        sa.Column("descrizione", sa.Text(), nullable=True),
        sa.Column("prezzo", sa.Float(), nullable=False),
        sa.Column("disponibile", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("immagine_etichetta", sa.String(512), nullable=True),
        sa.Column(
            "tipo",
            sa.Enum("rosso", "bianco", "rosato", "bollicine", name="tipo_vino"),
            nullable=False,
        ),
        sa.Column("vitigno", sa.String(255), nullable=True),
        sa.Column("caratteristiche_organolettiche", sa.JSON(), nullable=True),
        sa.Column("popolarita", sa.Integer(), nullable=True),
        sa.Column("scorte", sa.Integer(), nullable=True),
        sa.Column("dati_creazione", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("dati_aggiornamento", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_vini_nome", "vini", ["nome"])
    op.create_index("ix_vini_produttore", "vini", ["produttore"])
    op.create_index("ix_vini_regione", "vini", ["regione"])
    op.create_index("ix_vini_tipo", "vini", ["tipo"])

    op.create_table(
        "users",
        sa.Column("id", CHAR(36), primary_key=True),
        sa.Column("azure_oid", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("nome", sa.String(255), nullable=True),
        sa.Column(
            "ruolo",
            sa.Enum("admin", "user", name="user_role"),
            nullable=False,
            server_default="user",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("hashed_password", sa.String(255), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_users_azure_oid", "users", ["azure_oid"], unique=True)
    op.create_index("ix_users_email", "users", ["email"])


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_azure_oid", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_vini_tipo", table_name="vini")
    op.drop_index("ix_vini_regione", table_name="vini")
    op.drop_index("ix_vini_produttore", table_name="vini")
    op.drop_index("ix_vini_nome", table_name="vini")
    op.drop_table("vini")
