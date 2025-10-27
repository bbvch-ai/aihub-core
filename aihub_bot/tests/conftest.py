"""
Pytest configuration and shared fixtures.

This file makes fixtures available to all test modules.
"""

import sys
from pathlib import Path

# Add tests directory to path for imports
tests_dir = Path(__file__).parent
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))

# Import all fixtures from the fixtures module to make them available
from fixtures.bot_fixtures import (  # noqa: F401, E402
    mock_activity,
    mock_turn_context,
    slack_activity,
    teams_activity,
    webchat_activity,
)
