from unittest import TestCase

from google_play_scraper.utils.data_processors import unescape_text


class TestUnescapeText(TestCase):
    def test_br_variants(self):
        self.assertEqual(
            "a\r\nb\r\nc\r\nd\r\ne", unescape_text("a<br>b<br/>c<BR />d<br >e")
        )

    def test_strips_formatting_tags(self):
        self.assertEqual(
            "Bold, italic and underline",
            unescape_text("<b>Bold</b>, <i>italic</i> and <u>underline</u>"),
        )

    def test_link_keeps_url_after_text(self):
        self.assertEqual(
            "Visit our site (https://example.com/?a=1&b=2) now",
            unescape_text(
                'Visit <a href="https://example.com/?a=1&amp;b=2">our site</a> now'
            ),
        )

    def test_link_with_nested_tags(self):
        self.assertEqual(
            "Read the terms (https://example.com/tos).",
            unescape_text(
                '<a href="https://example.com/tos"><b>Read the <u>terms</u></b></a>.'
            ),
        )

    def test_link_text_edge_whitespace_stays_outside(self):
        self.assertEqual(
            "go here (https://a.com) now",
            unescape_text('go<a href="https://a.com"> here </a>now'),
        )
        self.assertEqual(
            "see it (https://a.com)\r\nnext",
            unescape_text('see <a href="https://a.com">it<br></a>next'),
        )

    def test_link_text_equal_to_url_is_not_duplicated(self):
        self.assertEqual(
            "See https://example.com",
            unescape_text('See <a href="https://example.com">https://example.com</a>'),
        )
        self.assertEqual(
            "See www.example.com",
            unescape_text('See <a href="https://www.example.com/">www.example.com</a>'),
        )
        self.assertEqual(
            "Mail help@example.com",
            unescape_text(
                'Mail <a href="mailto:help@example.com">help@example.com</a>'
            ),
        )

    def test_google_redirect_is_unwrapped(self):
        redirect = (
            "https://www.google.com/url?q=https%3A%2F%2Fweawow.com%2Fsearch"
            "&amp;sa=D&amp;sntz=1&amp;usg=stCLefDfmG0Vl9BC0Sbse6xLdG9l"
        )
        self.assertEqual(
            "Search (https://weawow.com/search)",
            unescape_text('<a href="{}">Search</a>'.format(redirect)),
        )
        self.assertEqual(
            "https://weawow.com/search",
            unescape_text(
                '<a href="{}">https://weawow.com/search</a>'.format(redirect)
            ),
        )

    def test_non_redirect_google_url_is_kept(self):
        self.assertEqual(
            "Paris (https://www.google.com/maps?q=paris)",
            unescape_text('<a href="https://www.google.com/maps?q=paris">Paris</a>'),
        )

    def test_link_without_text_shows_url(self):
        self.assertEqual(
            "Site: https://example.com",
            unescape_text('Site: <a href="https://example.com"></a>'),
        )

    def test_link_without_href_keeps_text(self):
        self.assertEqual("anchor text", unescape_text('<a name="x">anchor text</a>'))

    def test_unclosed_link(self):
        self.assertEqual(
            "go here (https://example.com)",
            unescape_text('go <a href="https://example.com">here'),
        )

    def test_unescapes_entities(self):
        self.assertEqual(
            "Tom & Jerry's \"fun\" café",
            unescape_text("Tom &amp; Jerry&#39;s &quot;fun&quot; caf&eacute;"),
        )

    def test_escaped_markup_is_kept_as_text(self):
        self.assertEqual("use <b> for bold", unescape_text("use &lt;b&gt; for bold"))

    def test_bare_angle_brackets_are_kept(self):
        self.assertEqual("1 < 2 and 3 > 2", unescape_text("1 < 2 and 3 > 2"))