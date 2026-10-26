from datetime import UTC, datetime

from swiss_ai_hub.agent.capabilities.web_fetch.fetched_web_page import WEB_NAMESPACE, FetchedWebPage

URL = "https://example.com/pricing"
FETCHED_AT = datetime(2026, 9, 24, 10, 30, tzinfo=UTC)


def _page(url: str = URL, markdown: str = "# Pricing", title: str | None = "Pricing") -> FetchedWebPage:
    return FetchedWebPage(url=url, title=title, markdown=markdown, fetched_at=FETCHED_AT)


class TestToIngestedNode:
    def test_maps_the_page_onto_a_source_chat_clients_link(self):
        node = _page().to_ingested_node()

        assert node.source == URL
        assert node.source_origin == URL
        assert node.document_title == "Pricing"
        assert node.content == "# Pricing"
        assert node.namespace == WEB_NAMESPACE

    def test_labels_a_page_without_a_title_by_its_url(self):
        assert _page(title=None).to_ingested_node().document_title == URL

    def test_a_refetched_page_keeps_its_citation_id(self):
        """The id comes from the URL alone, so the answer cites the page the same way on every turn."""
        first = _page(markdown="# First fetch").to_ingested_node()
        second = FetchedWebPage(url=URL, markdown="# Refetched").to_ingested_node()

        assert first.citation_id == second.citation_id

    def test_the_id_is_stable_across_processes(self):
        """A sha256 digest, not `hash()`, which differs between the agent processes that run consecutive steps."""
        node = _page().to_ingested_node()

        assert len(node.id) == 64
        int(node.id, 16)
        assert node.document_id == node.id

    def test_distinct_urls_get_distinct_citations(self):
        other = _page(url="https://example.com/about").to_ingested_node()

        assert _page().to_ingested_node().citation_id != other.citation_id

    def test_all_timestamps_are_the_fetch_time(self):
        """A fetched page has no ingestion history; the fetch time is the only honest value for all three."""
        node = _page().to_ingested_node()

        assert node.created_at == node.updated_at == node.inserted_at == FETCHED_AT.isoformat()
