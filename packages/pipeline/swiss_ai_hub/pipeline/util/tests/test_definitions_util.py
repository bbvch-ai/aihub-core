import warnings

from swiss_ai_hub.pipeline.util.definitions_util import resolve_encode_partition_keys


class TestResolveEncodePartitionKeys:
    def test_true_returns_true(self) -> None:
        assert resolve_encode_partition_keys(True) is True

    def test_false_returns_false(self) -> None:
        assert resolve_encode_partition_keys(False) is False

    def test_none_returns_false_with_deprecation_warning(self) -> None:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = resolve_encode_partition_keys(None)
            assert result is False
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "encode_partition_keys" in str(w[0].message)
