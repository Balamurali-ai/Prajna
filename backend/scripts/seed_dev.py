"""
====================================================
Seed Development Data
==================================================
Creates a development admin user and basic data
for local testing. NEVER run in production.
====================================================
"""
import asyncio
import sys
from pathlib import Path
from uuid import UUID

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.database import get_db, init_db, close_db  # noqa: E402
from app.database.models.user import User, UserRole, UserStatus  # noqa: E402
from sqlalchemy import select  # noqa: E402


async def seed():
    """Insert seed data."""
    await init_db()
    print("🌱 Seeding development data...")

    async for db in get_db():
        # Check existing
        result = await db.execute(
            select(User).where(User.email == "admin@crime-intel.gov")
        )
        existing = result.scalar_one_or_none()
        if existing:
            print("   Admin already exists, skipping")
            return

        # Create admin
        admin = User(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            supabase_user_id=UUID("00000000-0000-0000-0000-000000000001"),
            email="admin@crime-intel.gov",
            full_name="System Administrator",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            department="Command Center",
            badge_number="ADMIN-001",
        )
        db.add(admin)

        # Create officer
        officer = User(
            id=UUID("00000000-0000-0000-0000-000000000002"),
            supabase_user_id=UUID("00000000-0000-0000-0000-000000000002"),
            email="officer@crime-intel.gov",
            full_name="Demo Officer",
            role=UserRole.OFFICER,
            status=UserStatus.ACTIVE,
            department="Field Operations",
            badge_number="OFF-001",
        )
        db.add(officer)

        # Create analyst
        analyst = User(
            id=UUID("00000000-0000-0000-0000-000000000003"),
            supabase_user_id=UUID("00000000-0000-0000-0000-000000000003"),
            email="analyst@crime-intel.gov",
            full_name="Demo Analyst",
            role=UserRole.ANALYST,
            status=UserStatus.ACTIVE,
            department="Crime Analytics",
            badge_number="ANL-001",
        )
        db.add(analyst)

        await db.commit()
        print("   ✅ Created admin, officer, analyst")
        break

    await close_db()
    print("🎉 Seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed())
