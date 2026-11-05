from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_file import MediaWikiFile

_LISTED = {
    "pageid": 101,
    "title": "File:Handbook 2026.PDF",
    "imageinfo": {
        "url": "https://wiki.acme.test/images/a/ab/Handbook_2026.PDF",
        "descriptionurl": "https://wiki.acme.test/index.php/File:Handbook_2026.PDF",
        "size": 1234,
        "sha1": "abc123",
    },
}


def test_a_file_lands_under_its_name_with_a_lower_case_extension():
    """A listing and a write must agree on the key whatever case the uploader used."""
    file = MediaWikiFile.from_listing(_LISTED, "File")

    assert file.object_key == "File/Handbook 2026.pdf"
    assert file.fingerprint == "abc123|File/Handbook 2026.pdf"


def test_its_reference_cites_the_description_page_and_downloads_the_file():
    reference = MediaWikiFile.from_listing(_LISTED, "Datei").to_reference()

    assert reference.object_key == "Datei/Handbook 2026.pdf"
    assert reference.title == "Handbook 2026.PDF"
    assert reference.url == "https://wiki.acme.test/index.php/File:Handbook_2026.PDF"
    assert reference.download_url == "https://wiki.acme.test/images/a/ab/Handbook_2026.PDF"
    assert reference.metadata() == {
        "document_title": "Handbook 2026.PDF",
        "source_origin": "https://wiki.acme.test/index.php/File:Handbook_2026.PDF",
    }


def test_a_name_of_dots_before_its_extension_is_stored_under_its_id():
    """``..pdf`` is a valid wiki title but no file name; failing on it would stop every sync of the database."""
    file = MediaWikiFile.from_listing({**_LISTED, "title": "File:..pdf"}, "File")

    assert file.object_key == "File/file 101.pdf"
