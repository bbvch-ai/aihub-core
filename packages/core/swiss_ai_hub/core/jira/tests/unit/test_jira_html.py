from swiss_ai_hub.core.jira.jira_html import JiraHtml


class TestHtml:
    def test_tables_lists_and_code_survive(self):
        html = (
            "<h3>Steps</h3><ol><li>Open</li><li>Click</li></ol>"
            "<table><tbody><tr><th>Field</th><th>Value</th></tr><tr><td>a</td><td>1</td></tr></tbody></table>"
            '<div class="code panel"><div class="codeContent panelContent">'
            '<pre class="code-java">int x = 1;</pre></div></div>'
        )

        markdown = JiraHtml.to_markdown(html, "https://acme.atlassian.net")

        assert "### Steps" in markdown
        assert "1. Open\n2. Click" in markdown
        assert "| Field | Value |" in markdown
        assert "int x = 1;" in markdown

    def test_identifiers_keep_their_underscores_and_asterisks(self):
        """Escaped, ``ENG_CONFIG_PATH`` would be indexed as ``ENG\\_CONFIG\\_PATH`` and missed by a keyword search."""
        markdown = JiraHtml.to_markdown("<p>Set ENG_CONFIG_PATH and run *.sh in my_script.py</p>", "https://x.test")

        assert markdown == "Set ENG_CONFIG_PATH and run *.sh in my_script.py"

    def test_monospace_text_from_data_center_stays_code(self):
        markdown = JiraHtml.to_markdown("<p>Run <tt>make test</tt> first</p>", "https://jira.acme.ch/jira")

        assert markdown == "Run `make test` first"

    def test_relative_links_point_at_jira_and_keep_its_context_path(self):
        html = '<a href="/jira/browse/ABC-2">ABC-2</a> and <a href="https://example.com">site</a>'

        markdown = JiraHtml.to_markdown(html, "https://jira.acme.ch/jira")

        assert "[ABC-2](https://jira.acme.ch/jira/browse/ABC-2)" in markdown
        assert "[site](https://example.com)" in markdown

    def test_images_are_dropped_and_mentions_keep_only_the_name(self):
        html = (
            '<p><span class="image-wrap"><img src="/secure/attachment/1/a.png"></span>'
            '<a href="/secure/ViewProfile.jspa?accountId=5b10" class="user-hover" rel="5b10">Ada Lovelace</a>'
            " agreed</p>"
        )

        markdown = JiraHtml.to_markdown(html, "https://acme.atlassian.net")

        assert markdown == "Ada Lovelace agreed"

    def test_nothing_rendered_gives_nothing(self):
        assert JiraHtml.to_markdown(None, "https://acme.atlassian.net") == ""
        assert JiraHtml.to_markdown("  ", "https://acme.atlassian.net") == ""
