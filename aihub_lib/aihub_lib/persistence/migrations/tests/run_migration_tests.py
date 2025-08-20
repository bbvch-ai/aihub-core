"""
Migration test runner with pre-flight checks and comprehensive validation.

Provides a convenient way to run migration tests with proper setup validation
and clear reporting of results.
"""

import asyncio
import subprocess
import sys
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError


async def check_mongodb_connection(mongodb_url: str = "mongodb://admin:admin@localhost:27017") -> bool:
    """Check if MongoDB is accessible."""
    try:
        client = AsyncIOMotorClient(mongodb_url, serverSelectionTimeoutMS=5000)
        await client.admin.command("ping")
        client.close()
        return True
    except (ServerSelectionTimeoutError, Exception):
        return False


def run_command(cmd: list[str]) -> int:
    """Run command and return exit code."""
    print(f"🚀 Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent)
    return result.returncode


async def main():
    """Main test runner with validation steps."""
    print("🧪 AI-Hub Migration Test Runner")
    print("=" * 50)

    # Step 1: Check MongoDB connectivity
    print("\n📡 Checking MongoDB connectivity...")
    mongodb_available = await check_mongodb_connection()

    if not mongodb_available:
        print("❌ MongoDB not available at mongodb://admin:admin@localhost:27017")
        print("   Please ensure MongoDB is running:")
        print("   docker compose -f docker-compose.dev.yml up -d")
        print("\n⚠️  Migration tests require MongoDB to run properly")
        return 1
    else:
        print("✅ MongoDB connection successful")

    # Step 2: Run all migration tests
    print("\n🔬 Running migration tests...")
    test_cmd = ["poetry", "run", "pytest", "aihub_lib/persistence/migrations/tests/", "-v"]

    test_result = run_command(test_cmd)
    if test_result != 0:
        print("❌ Migration tests failed!")
        return test_result

    print("✅ Migration tests passed")

    # Step 3: Summary
    print("\n🎉 Migration Test Summary")
    print("=" * 30)
    print("✅ All migration tests: PASSED")
    print("\n🚀 Migration system is ready for production!")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)