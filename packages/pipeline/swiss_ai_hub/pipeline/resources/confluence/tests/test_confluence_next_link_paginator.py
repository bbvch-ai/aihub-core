import json

import pytest
from requests import Response

from swiss_ai_hub.pipeline.resources.confluence.confluence_next_link_paginator import (
    ConfluenceNextLinkPaginator,
)


def _response(links: dict[str, str]) -> Response:
    response = Response()
    response.status_code = 200
    response._content = json.dumps({"results": [], "_links": links}).encode()
    response.encoding = "utf-8"
    return response


@pytest.mark.parametrize(
    ("site_url", "next_link", "expected"),
    [
        (
            "https://example.atlassian.net/wiki",
            "/rest/api/content/search?cursor=a",
            "https://example.atlassian.net/wiki/rest/api/content/search?cursor=a",
        ),
        (
            "https://confluence.example.com",
            "/rest/api/content/search?start=50",
            "https://confluence.example.com/rest/api/content/search?start=50",
        ),
    ],
)
def test_a_path_is_followed_below_the_site(site_url: str, next_link: str, expected: str):
    paginator = ConfluenceNextLinkPaginator(site_url)

    paginator.update_state(_response({"base": site_url, "next": next_link}))

    assert (paginator.has_next_page, paginator._next_reference) == (True, expected)


def test_the_last_page_has_no_next_link():
    paginator = ConfluenceNextLinkPaginator("https://confluence.example.com")

    paginator.update_state(_response({"base": "https://confluence.example.com"}))

    assert paginator.has_next_page is False


@pytest.mark.parametrize(
    "next_link",
    [
        "@elsewhere.test/rest/api/content/search",
        ".elsewhere.test/rest/api/content/search",
        ":8443/rest/api/content/search",
        "//elsewhere.test/rest/api/content/search",
        "https://elsewhere.test/rest/api/content/search",
        "rest/api/content/search",
    ],
)
def test_a_link_that_would_leave_the_site_is_refused(next_link: str):
    """A site without a path is the easy case to bend: the link is appended right after the host."""
    paginator = ConfluenceNextLinkPaginator("https://confluence.example.com")
    response = _response({"base": "https://confluence.example.com", "next": next_link})

    with pytest.raises(ValueError, match="next page outside the site"):
        paginator.update_state(response)
