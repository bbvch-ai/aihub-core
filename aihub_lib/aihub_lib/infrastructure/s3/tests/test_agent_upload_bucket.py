from aihub_lib.infrastructure.s3.AgentFileUploadService import AgentFileUploadService


class TestAgentUploadBucketName:
    def test_basic_name(self):
        result = AgentFileUploadService.bucket_name("MyAgent", "instance-1")
        assert result == "agent-files-myagent-instance-1"

    def test_lowercases_everything(self):
        result = AgentFileUploadService.bucket_name("CamelCaseAgent", "ID_123")
        assert result == "agent-files-camelcaseagent-id-123"

    def test_replaces_underscores_with_hyphens(self):
        result = AgentFileUploadService.bucket_name("my_agent", "my_id")
        assert result == "agent-files-my-agent-my-id"

    def test_replaces_special_characters(self):
        result = AgentFileUploadService.bucket_name("agent@class!", "id#1")
        assert result == "agent-files-agent-class-id-1"

    def test_collapses_consecutive_hyphens(self):
        result = AgentFileUploadService.bucket_name("agent--class", "id--1")
        assert result == "agent-files-agent-class-id-1"

    def test_strips_leading_trailing_hyphens(self):
        result = AgentFileUploadService.bucket_name("-agent-", "-id-")
        assert result == "agent-files-agent-id"

    def test_minimum_length_padding(self):
        result = AgentFileUploadService.bucket_name("", "")
        assert len(result) >= 3

    def test_truncates_to_63_characters(self):
        long_class = "a" * 50
        long_id = "b" * 50
        result = AgentFileUploadService.bucket_name(long_class, long_id)
        assert len(result) <= 63

    def test_truncation_does_not_end_with_hyphen(self):
        long_class = "a" * 30
        long_id = "b-" * 30
        result = AgentFileUploadService.bucket_name(long_class, long_id)
        assert not result.endswith("-")

    def test_dots_replaced(self):
        result = AgentFileUploadService.bucket_name("agent.class", "id.1")
        assert result == "agent-files-agent-class-id-1"

    def test_deterministic(self):
        """Same inputs always produce the same bucket name."""
        a = AgentFileUploadService.bucket_name("TestAgent", "prod-1")
        b = AgentFileUploadService.bucket_name("TestAgent", "prod-1")
        assert a == b
