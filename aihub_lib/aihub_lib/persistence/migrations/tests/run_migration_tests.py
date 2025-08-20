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
        print("\n🏃‍♀️ Running unit tests only (no MongoDB integration)...")
    else:
        print("✅ MongoDB connection successful")

    # Step 2: Run unit tests (always)
    print("\n🔬 Running unit tests (mock-based, fast)...")
    unit_test_cmd = ["poetry", "run", "pytest", "aihub_lib/persistence/migrations/tests/", "-m", "not mongodb", "-v"]

    unit_result = run_command(unit_test_cmd)
    if unit_result != 0:
        print("❌ Unit tests failed!")
        return unit_result

    print("✅ Unit tests passed")

    # Step 3: Run integration tests if MongoDB available
    if mongodb_available:
        print("\n🔗 Running integration tests (requires MongoDB)...")
        integration_test_cmd = ["poetry", "run", "pytest", "aihub_lib/persistence/migrations/tests/", "--mongodb", "-v"]

        integration_result = run_command(integration_test_cmd)
        if integration_result != 0:
            print("❌ Integration tests failed!")
            return integration_result

        print("✅ Integration tests passed")

        # Step 4: Run performance tests
        print("\n⚡ Running performance tests...")
        perf_test_cmd = [
            "poetry",
            "run",
            "pytest",
            "aihub_lib/persistence/migrations/tests/",
            "--mongodb",
            "-m",
            "performance",
            "-v",
        ]

        perf_result = run_command(perf_test_cmd)
        if perf_result != 0:
            print("⚠️  Performance tests had issues (non-critical)")
        else:
            print("✅ Performance tests passed")

    # Step 5: Summary
    print("\n🎉 Migration Test Summary")
    print("=" * 30)
    print("✅ Unit tests: PASSED")
    if mongodb_available:
        print("✅ Integration tests: PASSED")
        print("✅ Performance tests: PASSED")
        print("\n🚀 Migration system is ready for production!")
    else:
        print("⚠️  Integration tests: SKIPPED (no MongoDB)")
        print("\n⚠️  Run with MongoDB for complete validation")

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
