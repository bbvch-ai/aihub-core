import pytest

from swiss_ai_hub.core.topics import RpcTopic, Topic


class TestRpcTopic:
    def test_from_subject_agent_config(self) -> None:
        topic = RpcTopic.from_subject("aihub.rpc.config.agent.RAGAgent.default")
        assert topic.service == "config"
        assert topic.entity_type == "agent"
        assert topic.entity_class == "RAGAgent"
        assert topic.entity_id == "default"

    def test_from_subject_process_config(self) -> None:
        topic = RpcTopic.from_subject("aihub.rpc.config.process.Onboarding.hr")
        assert topic.service == "config"
        assert topic.entity_type == "process"
        assert topic.entity_class == "Onboarding"
        assert topic.entity_id == "hr"

    def test_to_subject(self) -> None:
        topic = RpcTopic(
            service="config",
            entity_type="agent",
            entity_class="RAGAgent",
            entity_id="default",
        )
        assert topic.to_subject() == "aihub.rpc.config.agent.RAGAgent.default"

    def test_execution_context_id(self) -> None:
        topic = RpcTopic(
            service="config",
            entity_type="agent",
            entity_class="RAGAgent",
            entity_id="default",
        )
        assert topic.execution_context_id == "RAGAgent.default"

    def test_invalid_subject_wrong_prefix(self) -> None:
        with pytest.raises(ValueError, match="Not an RPC topic"):
            RpcTopic.from_subject("agent.chatbot.x.y.z.w")

    def test_invalid_subject_wrong_segment_count(self) -> None:
        with pytest.raises(ValueError, match="must have 6 segments"):
            RpcTopic.from_subject("aihub.rpc.config.agent.RAGAgent")

    def test_invalid_subject_too_many_segments(self) -> None:
        with pytest.raises(ValueError, match="must have 6 segments"):
            RpcTopic.from_subject("aihub.rpc.config.agent.RAGAgent.default.extra")

    def test_topic_auto_registration(self) -> None:
        """RpcTopic should be discoverable via Topic.from_subject()."""
        topic = Topic.from_subject("aihub.rpc.config.agent.RAGAgent.default")
        assert isinstance(topic, RpcTopic)
        assert topic.service == "config"
        assert topic.entity_type == "agent"

    def test_roundtrip(self) -> None:
        """Parse a subject, convert back to subject, should match."""
        original = "aihub.rpc.config.process.Workflow.instance-1"
        topic = RpcTopic.from_subject(original)
        assert topic.to_subject() == original
