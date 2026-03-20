from app.services.rss_service import RSSIngestService


def test_extract_focus_text_from_html_keeps_headings_and_paragraphs_only():
    html = """
    <html>
      <head>
        <title>ignored</title>
        <style>.x { color: red; }</style>
        <script>console.log('ignored');</script>
      </head>
      <body>
        <nav>menu should be ignored</nav>
        <h1>Main Title</h1>
        <div>
          <h2>Section A</h2>
          <p>First <b>paragraph</b>.</p>
          <p>Second&nbsp;paragraph.</p>
        </div>
        <footer>ignored footer</footer>
      </body>
    </html>
    """

    result = RSSIngestService._extract_focus_text_from_html(html)
    print(result)

    assert result == "\n".join(
        [
            "<h1>Main Title</h1>",
            "<h2>Section A</h2>",
            "First paragraph.",
            "Second paragraph.",
        ]
    )


def test_extract_focus_text_from_html_returns_empty_when_no_target_tags():
    html = "<html><body><div>only div</div><span>only span</span></body></html>"

    result = RSSIngestService._extract_focus_text_from_html(html)

    assert result == ""


def test_extract_focus_text_from_html_preserves_table_row_and_cell_structure():
    html = """
    <html>
      <body>
        <h2>Metrics</h2>
        <p>Summary intro.</p>
        <table>
          <tr><th>Key</th><th>Value</th></tr>
          <tr><td>Users</td><td>1200</td></tr>
          <tr><td>Growth</td><td>12%</td></tr>
        </table>
      </body>
    </html>
    """

    result = RSSIngestService._extract_focus_text_from_html(html)

    assert result == "\n".join(
        [
            "<h2>Metrics</h2>",
            "Summary intro.",
            "Key\tValue",
            "Users\t1200",
            "Growth\t12%",
        ]
    )


def test_extract_focus_text_from_html_cleans_redundant_tabs_and_whitespace_in_table():
    html = """
    <html>
      <body>
        <p>Table below</p>
        <table>
          <tr>
            <td> A </td>
            <td>  B  </td>
            <td> C </td>
          </tr>
        </table>
      </body>
    </html>
    """

    result = RSSIngestService._extract_focus_text_from_html(html)

    assert result == "\n".join(["Table below", "A\tB\tC"])
