from swiss_ai_hub.pipeline.source_pipelines.mediawiki.mediawiki_html import MediaWikiHtml

_PAGE = "https://wiki.acme.test/index.php/Events/Dev_Day"


def _markdown(html: str) -> str:
    return MediaWikiHtml.to_markdown(f'<div class="mw-parser-output">{html}</div>', _PAGE)


def test_empty_html_is_no_text():
    assert MediaWikiHtml.to_markdown(None, _PAGE) == ""
    assert MediaWikiHtml.to_markdown("  ", _PAGE) == ""


def test_headings_lists_and_emphasis_become_markdown():
    html = (
        '<div class="mw-heading mw-heading2"><h2 id="Goals">Goals</h2></div>'
        "<p><b>Why:</b> meet people</p><ul><li>one</li><li>two</li></ul>"
    )

    assert _markdown(html) == "## Goals\n\n**Why:** meet people\n\n- one\n- two"


def test_page_chrome_and_parser_comments_are_dropped():
    html = (
        '<h2><span class="mw-headline">Agenda</span><span class="mw-editsection">[edit]</span></h2>'
        '<div id="toc" class="toc"><ul><li>1 Agenda</li></ul></div>'
        '<p class="mw-empty-elt"></p><table class="navbox"><tr><td>Events</td></tr></table>'
        "<style>.x{}</style><!-- NewPP limit report -->"
        "<p>Talks start at nine.</p>"
    )

    assert _markdown(html) == "## Agenda\n\nTalks start at nine."


def test_links_become_absolute_against_the_page_and_red_links_keep_their_text():
    html = (
        '<p><a href="/index.php/Venue" title="Venue">Venue</a>, <a href="#Agenda">agenda</a>, '
        '<a class="new" href="/index.php?title=Speakers&amp;action=edit&amp;redlink=1">speakers</a>, '
        '<a rel="nofollow" class="external text" href="https://devday.example">site</a></p>'
    )

    assert _markdown(html) == (
        "[Venue](https://wiki.acme.test/index.php/Venue), "
        "[agenda](https://wiki.acme.test/index.php/Events/Dev_Day#Agenda), speakers, [site](https://devday.example)"
    )


def test_images_and_the_links_wrapping_them_are_dropped():
    html = (
        '<figure><a href="/index.php/File:Logo.png" class="mw-file-description"><img src="/images/logo.png"></a>'
        "<figcaption>The logo</figcaption></figure><p>Text</p>"
    )

    assert _markdown(html) == "The logo\n\nText"


def test_unset_template_parameters_are_dropped():
    assert _markdown("<p>Engagement: {{{engagement}}}, budget {{{budget|}}}</p>") == "Engagement: , budget"


def test_identifiers_keep_their_underscores_and_asterisks():
    assert _markdown("<p>Set ENG_CONFIG_PATH to *.yml</p>") == "Set ENG_CONFIG_PATH to *.yml"


def test_an_infobox_becomes_a_wrapped_markdown_table():
    """The chunker recognises a table only inside the <table> wrapper the converter writes."""
    html = (
        '<table class="infobox"><tr><th>Field</th><th>Value</th></tr>'
        "<tr><td>Date</td><td>2020-06-08</td></tr><tr><td>Lead</td><td>Ada</td></tr></table>"
        "<p>After</p>"
    )

    markdown = _markdown(html)

    assert markdown.startswith("<table>| Field | Value |\n| --- | --- |\n| Date | 2020-06-08 |\n| Lead | Ada |</table>")
    assert markdown.endswith("After")


def test_a_frame_around_a_table_is_unwrapped_and_the_inner_table_kept():
    """A process header frames its content and a data table in one outer table; as data it would be a single cell."""
    html = (
        "<table><tr><td><p>The overview of all processes.</p>"
        '<table class="wikitable"><tr><th>No</th><th>Process</th></tr><tr><td>P00</td><td>Strategy</td></tr></table>'
        "</td></tr></table>"
    )

    assert _markdown(html) == (
        "The overview of all processes.\n\n<table>| No | Process |\n| --- | --- |\n| P00 | Strategy |</table>"
    )


def test_a_single_row_table_is_layout_and_its_cells_become_blocks():
    html = (
        '<table class="messagebox"><tr><td><b>Note</b></td>'
        "<td><ul><li>Kept up to date by HR</li></ul></td></tr></table>"
    )

    assert _markdown(html) == "**Note**\n\n- Kept up to date by HR"


def test_a_page_mentioning_the_table_marker_keeps_its_text_and_its_tables():
    """A fixed marker in the page's own text would crash the conversion or put a table in the wrong place."""
    markdown = _markdown(
        "<p>See MEDIAWIKITABLE3 and MEDIAWIKITABLE0.</p>"
        "<table><tr><th>Step</th><th>Owner</th></tr><tr><td>Plan</td><td>PM</td></tr></table>"
    )

    assert "See MEDIAWIKITABLE3 and MEDIAWIKITABLE0." in markdown
    assert markdown.count("Plan") == 1
