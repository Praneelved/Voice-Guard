"""enable_rls

Revision ID: 6dd3569fc56d
Revises: 35410e2c1e5c
Create Date: 2026-09-23 01:44:31.814422

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6dd3569fc56d'
down_revision: Union[str, Sequence[str], None] = '35410e2c1e5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # We execute raw SQL to enable RLS and add policies since SQLAlchemy/Alembic don't do this natively
    op.execute("ALTER TABLE call_sessions ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE risk_events ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE trusted_voices ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE protected_numbers ENABLE ROW LEVEL SECURITY;")
        
    # Policies
    op.execute("""
        CREATE POLICY "Users can only access their own calls" ON call_sessions
            FOR ALL USING (auth.uid() = org_id);
    """)
            
    op.execute("""
        CREATE POLICY "Users can only access risk events for their calls" ON risk_events
            FOR ALL USING (
                call_id IN (SELECT id FROM call_sessions WHERE auth.uid() = org_id)
            );
    """)
            
    op.execute("""
        CREATE POLICY "Users can only access alerts for their calls" ON alerts
            FOR ALL USING (
                call_id IN (SELECT id FROM call_sessions WHERE auth.uid() = org_id)
            );
    """)
            
    op.execute("""
        CREATE POLICY "Users can only access their trusted voices" ON trusted_voices
            FOR ALL USING (auth.uid() = user_id);
    """)
            
    op.execute("""
        CREATE POLICY "Users can only access their protected numbers" ON protected_numbers
            FOR ALL USING (auth.uid() = user_id);
    """)

def downgrade() -> None:
    """Downgrade schema."""
    op.execute('DROP POLICY IF EXISTS "Users can only access their own calls" ON call_sessions;')
    op.execute('DROP POLICY IF EXISTS "Users can only access risk events for their calls" ON risk_events;')
    op.execute('DROP POLICY IF EXISTS "Users can only access alerts for their calls" ON alerts;')
    op.execute('DROP POLICY IF EXISTS "Users can only access their trusted voices" ON trusted_voices;')
    op.execute('DROP POLICY IF EXISTS "Users can only access their protected numbers" ON protected_numbers;')
        
    op.execute("ALTER TABLE call_sessions DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE risk_events DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE alerts DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE trusted_voices DISABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE protected_numbers DISABLE ROW LEVEL SECURITY;")
