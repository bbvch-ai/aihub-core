import pytest

from swiss_ai_hub.pipeline.source_pipelines.confluence.confluence_storage import ConfluenceStorage

_SITE = "https://acme.atlassian.net/wiki"


def _markdown(storage: str | None) -> str:
    return ConfluenceStorage.to_markdown(storage, _SITE)


class TestText:
    @pytest.mark.parametrize("storage", [None, "", "  \n "])
    def test_an_empty_body_is_empty(self, storage: str | None):
        assert _markdown(storage) == ""

    def test_headings_paragraphs_and_lists_survive(self):
        storage = (
            "<h1>Overview</h1><p>Deploy <strong>carefully</strong>.</p>"
            "<h2>Steps</h2><ol><li>Build</li><li>Ship</li></ol><ul><li>Monday</li><li>Friday</li></ul>"
        )

        assert _markdown(storage) == (
            "# Overview\n\nDeploy **carefully**.\n\n## Steps\n\n1. Build\n2. Ship\n\n- Monday\n- Friday"
        )

    def test_identifiers_keep_their_underscores_and_asterisks(self):
        """Escaped, ``ENG_CONFIG_PATH`` would be indexed as ``ENG\\_CONFIG\\_PATH`` and not be found as written."""
        assert _markdown("<p>Set ENG_CONFIG_PATH for *.yaml files</p>") == "Set ENG_CONFIG_PATH for *.yaml files"

    def test_non_breaking_spaces_become_spaces(self):
        assert _markdown("<p>Version&nbsp;2</p>") == "Version 2"

    def test_a_date_keeps_its_value(self):
        assert _markdown('<p>Due <time datetime="2026-11-01" /></p>') == "Due 2026-11-01"

    def test_an_element_dropped_mid_sentence_keeps_the_words_apart(self):
        """markdownify strips the whitespace around an empty string, which would glue the neighbours together."""
        storage = (
            '<p>Ship <ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">Grey</ac:parameter>'
            '</ac:structured-macro> today, <time datetime="" /> maybe.</p>'
        )

        assert _markdown(storage).split() == ["Ship", "today,", "maybe."]


class TestMacros:
    def test_a_code_macro_becomes_a_fenced_block_with_its_language(self):
        storage = (
            '<ac:structured-macro ac:name="code"><ac:parameter ac:name="language">python</ac:parameter>'
            '<ac:plain-text-body><![CDATA[if a < b:\n    print("*")]]></ac:plain-text-body></ac:structured-macro>'
        )

        assert _markdown(storage) == '```python\nif a < b:\n    print("*")\n```'

    def test_a_noformat_block_becomes_a_fenced_block_without_a_language(self):
        storage = (
            '<ac:structured-macro ac:name="noformat"><ac:plain-text-body><![CDATA[GET /health]]>'
            "</ac:plain-text-body></ac:structured-macro>"
        )

        assert _markdown(storage) == "```\nGET /health\n```"

    def test_a_panel_keeps_its_body_under_its_title_and_nested_macros_are_rewritten(self):
        storage = (
            '<ac:structured-macro ac:name="info"><ac:parameter ac:name="title">Heads up</ac:parameter>'
            "<ac:rich-text-body><p>Read this first.</p></ac:rich-text-body></ac:structured-macro>"
            '<ac:structured-macro ac:name="expand"><ac:parameter ac:name="title">Details</ac:parameter>'
            '<ac:rich-text-body><ac:structured-macro ac:name="code"><ac:plain-text-body><![CDATA[make deploy]]>'
            "</ac:plain-text-body></ac:structured-macro></ac:rich-text-body></ac:structured-macro>"
        )

        assert _markdown(storage) == "**Heads up**\n\nRead this first.\n\n**Details**\n\n```\nmake deploy\n```"

    def test_a_status_lozenge_keeps_its_title(self):
        storage = (
            '<p>Status: <ac:structured-macro ac:name="status"><ac:parameter ac:name="colour">Green</ac:parameter>'
            '<ac:parameter ac:name="title">DONE</ac:parameter></ac:structured-macro></p>'
        )

        assert _markdown(storage) == "Status: DONE"

    def test_macros_that_only_render_something_elsewhere_are_dropped(self):
        storage = (
            '<p>Intro</p><ac:structured-macro ac:name="toc"><ac:parameter ac:name="maxLevel">3</ac:parameter>'
            '</ac:structured-macro><ac:structured-macro ac:name="jira"><ac:parameter ac:name="key">ENG-42'
            '</ac:parameter></ac:structured-macro><ac:structured-macro ac:name="children" />'
        )

        assert _markdown(storage) == "Intro"

    def test_a_task_list_keeps_what_is_done(self):
        storage = (
            "<ac:task-list><ac:task><ac:task-id>1</ac:task-id><ac:task-status>incomplete</ac:task-status>"
            "<ac:task-body>Write docs</ac:task-body></ac:task><ac:task><ac:task-id>2</ac:task-id>"
            "<ac:task-status>complete</ac:task-status><ac:task-body>Ship</ac:task-body></ac:task></ac:task-list>"
        )

        assert _markdown(storage) == "- [ ] Write docs\n- [x] Ship"

    def test_a_cloud_element_stored_as_adf_keeps_its_fallback(self):
        storage = (
            '<ac:adf-extension><ac:adf-node type="decision-list"><ac:adf-node type="decision-item">'
            "<ac:adf-content>We use Postgres</ac:adf-content></ac:adf-node></ac:adf-node>"
            "<ac:adf-fallback><ul><li>We use Postgres</li></ul></ac:adf-fallback></ac:adf-extension>"
        )

        assert _markdown(storage) == "- We use Postgres"

    def test_a_layout_keeps_its_cells_in_order(self):
        storage = (
            '<ac:layout><ac:layout-section ac:type="two_equal"><ac:layout-cell><p>Left</p></ac:layout-cell>'
            "<ac:layout-cell><p>Right</p></ac:layout-cell></ac:layout-section></ac:layout>"
        )

        assert _markdown(storage) == "Left\n\nRight"


class TestTables:
    def test_a_table_is_wrapped_so_the_chunker_and_refiner_recognise_it(self):
        storage = (
            '<p>Team</p><table class="wrapped"><colgroup><col /><col /></colgroup><tbody>'
            "<tr><th><p>Name</p></th><th><p>Role</p></th></tr>"
            "<tr><td><p>Ada</p></td><td><p>Engineer</p></td></tr></tbody></table><p>End</p>"
        )

        assert _markdown(storage) == (
            "Team\n\n<table>| Name | Role |\n| --- | --- |\n| Ada | Engineer |</table>\n\nEnd"
        )

    def test_a_merged_cell_is_repeated_across_its_columns(self):
        storage = "<table><tbody><tr><th>Q1</th><th>Q2</th></tr><tr><td colspan='2'>Frozen</td></tr></tbody></table>"

        assert "| Frozen | Frozen |" in _markdown(storage)

    def test_a_table_nested_in_a_cell_is_read_as_that_cells_text(self):
        storage = (
            "<table><tbody><tr><th>Area</th><th>Owners</th></tr><tr><td>API</td><td>"
            "<table><tbody><tr><td>Ada</td><td>Grace</td></tr></tbody></table></td></tr></tbody></table>"
        )

        markdown = _markdown(storage)

        assert markdown.count("<table>") == 1
        assert "| API | Ada Grace |" in markdown

    def test_every_table_of_a_page_with_more_than_ten_stays_in_its_place(self):
        """The eleventh table's marker starts with the second's; replacing one must not take the other."""
        storage = "".join(
            f"<p>Section {index}</p><table><tbody><tr><th>Table</th></tr><tr><td>T{index}</td></tr></tbody></table>"
            for index in range(12)
        )

        sections = _markdown(storage).split("Section ")[1:]

        assert [section.split("\n", 1)[0] for section in sections] == [str(index) for index in range(12)]
        assert all(f"| T{index} |" in section for index, section in enumerate(sections))


class TestLinksAndImages:
    def test_a_link_to_another_page_keeps_its_text(self):
        storage = (
            '<p>See <ac:link><ri:page ri:content-title="Runbook" /><ac:plain-text-link-body><![CDATA[the runbook]]>'
            '</ac:plain-text-link-body></ac:link> and <ac:link><ri:page ri:content-title="Glossary" /></ac:link>.</p>'
        )

        assert _markdown(storage) == "See the runbook and Glossary."

    def test_web_links_are_absolute(self):
        storage = '<p><a href="https://example.com/docs">Docs</a> and <a href="/wiki/spaces/ENG/pages/7">a page</a></p>'

        assert _markdown(storage) == (
            "[Docs](https://example.com/docs) and [a page](https://acme.atlassian.net/wiki/spaces/ENG/pages/7)"
        )

    def test_a_user_mention_never_writes_an_account_id(self):
        storage = '<p>Ask <ac:link><ri:user ri:account-id="557058:f0a1b2c3" /></ac:link> first.</p>'

        markdown = _markdown(storage)

        assert "557058" not in markdown
        assert markdown.split() == ["Ask", "first."]

    def test_images_and_attachments_are_dropped_but_a_link_text_stays(self):
        storage = (
            '<p>Diagram: <ac:image><ri:attachment ri:filename="diagram.png" /></ac:image><img src="x.png" /></p>'
            '<p><ac:link><ri:attachment ri:filename="plan.pdf" /><ac:plain-text-link-body><![CDATA[the plan]]>'
            "</ac:plain-text-link-body></ac:link></p>"
        )

        assert _markdown(storage) == "Diagram:\n\nthe plan"
