"""
Test script for Slack Direct API integration with ExpertAskingAgent
This script validates the core Slack functionality without running the full agent workflow.
"""

import asyncio
import os

from SlackDirectClient import SlackDirectClient
from SlackResponsePoller import SlackResponsePoller


async def test_slack_integration():
    """Test basic Slack API functionality"""

    # Get token from environment (for testing only)
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    if not slack_token:
        print("❌ SLACK_BOT_TOKEN environment variable not set")
        return False

    # Get test channel from environment
    test_channel = os.getenv("SLACK_TEST_CHANNEL")
    if not test_channel:
        print("❌ SLACK_TEST_CHANNEL environment variable not set")
        return False

    try:
        # Initialize client
        client = SlackDirectClient(slack_token)
        print("✅ Slack client initialized")

        # Test posting a message
        test_message = "🤖 Testing direct Slack API integration for Expert Agent"
        response = await client.post_message(test_channel, test_message)
        message_ts = response["ts"]
        print(f"✅ Message posted successfully: {message_ts}")

        # Test getting channel history
        history = await client.get_channel_history(test_channel, limit=5)
        print(f"✅ Retrieved {len(history.get('messages', []))} recent messages")

        # Test response polling (with short timeout for testing)
        print("⏳ Testing response polling (10 second timeout)...")
        poller = SlackResponsePoller(client, poll_interval=2)

        try:
            responses = await poller.wait_for_response(channel=test_channel, message_ts=message_ts, timeout=10)
            if responses:
                print(f"✅ Received {len(responses)} responses")
                for resp in responses:
                    print(f"  - {resp.username}: {resp.text[:50]}...")
            else:
                print("ℹ️  No responses received (expected for automated test)")

        except TimeoutError:
            print("ℹ️  Polling timeout reached (expected for automated test)")

        print("✅ All Slack API tests completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_error_handling():
    """Test error handling with invalid credentials"""

    try:
        # Test with invalid token
        client = SlackDirectClient("invalid-token")
        await client.post_message("C1234567890", "test")
        print("❌ Should have failed with invalid token")
        return False

    except ValueError as e:
        if "Slack API error" in str(e):
            print("✅ Error handling works correctly for invalid token")
            return True
        else:
            print(f"❌ Unexpected error: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected exception type: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting Slack Direct API Integration Tests")
    print("=" * 50)

    async def run_tests():
        # Test basic functionality
        basic_test_passed = await test_slack_integration()

        # Test error handling
        error_test_passed = await test_error_handling()

        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        print(f"  Basic Integration: {'✅ PASS' if basic_test_passed else '❌ FAIL'}")
        print(f"  Error Handling: {'✅ PASS' if error_test_passed else '❌ FAIL'}")

        if basic_test_passed and error_test_passed:
            print("\n🎉 All tests passed! Slack integration is ready.")
        else:
            print("\n⚠️  Some tests failed. Please check the configuration.")

    asyncio.run(run_tests())
