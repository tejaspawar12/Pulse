"""fix normalized_name unique constraint

Revision ID: a1b2c3d4e5f6
Revises: dd178888e641
Create Date: 2026-01-20 09:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'dd178888e641'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old unique index on normalized_name alone
    op.execute("DROP INDEX IF EXISTS uq_exercise_normalized_name;")
    
    # Create new unique index on (normalized_name, equipment)
    # This allows multiple exercises with same normalized name but different equipment
    # e.g., "Shrugs" (barbell), "Shrugs" (dumbbell), "Shrugs" (machine)
    op.execute("""
        CREATE UNIQUE INDEX uq_exercise_unique 
        ON exercise_library(normalized_name, equipment);
    """)


def downgrade() -> None:
    # Drop the new composite unique index
    op.execute("DROP INDEX IF EXISTS uq_exercise_unique;")
    
    # Restore the old unique index on normalized_name alone
    op.execute("""
        CREATE UNIQUE INDEX uq_exercise_normalized_name 
        ON exercise_library(normalized_name);
    """)
