import pytest

from swiss_ai_hub.core.testing.tests.unit.beanie_probe_document import BeanieProbeDocument

pytestmark = pytest.mark.beanie


async def test_reads_back_a_document_written_through_the_session_client() -> None:
    await BeanieProbeDocument(key="written").insert()

    found = await BeanieProbeDocument.find_one(BeanieProbeDocument.key == "written")

    assert found is not None
    assert found.key == "written"


@pytest.mark.parametrize("key", ["first", "second"])
async def test_starts_without_documents_from_earlier_tests(key: str) -> None:
    """Both cases write one document, so whichever runs second sees two if isolation fails."""
    await BeanieProbeDocument(key=key).insert()

    assert await BeanieProbeDocument.count() == 1
