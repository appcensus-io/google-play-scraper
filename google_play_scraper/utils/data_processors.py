from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import parse_qs, urlsplit


class _Link:
    """An ``<a href>`` element and its visible text, rendered as plain text."""

    def __init__(self, href: str, text: str) -> None:
        self.url = self._unwrap_google_redirect(href)
        self.text = text

    def to_text(self) -> str:
        """Return ``text (url)``, just ``url`` when the text is empty, or just
        the text when it already shows the URL. Whitespace at the edges of the
        text is kept outside the result, so ``" here "`` gives
        ``" here (url) "``."""
        core = self.text.strip()
        lead = self.text[: len(self.text) - len(self.text.lstrip())]
        trail = self.text[len(lead) + len(core) :]

        if not core:
            rendered = self.url
        elif self._strip_url_decorations(core) == self._strip_url_decorations(self.url):
            rendered = core
        else:
            rendered = "{} ({})".format(core, self.url)
        return lead + rendered + trail

    @staticmethod
    def _unwrap_google_redirect(url: str) -> str:
        """External links in Play descriptions usually arrive wrapped in a Google
        redirect like
        ``https://www.google.com/url?q=https%3A%2F%2Fexample.com&sa=D&usg=...``;
        return the real destination instead. Other URLs are returned unchanged."""
        parts = urlsplit(url)
        if parts.hostname in ("google.com", "www.google.com") and parts.path == "/url":
            params = parse_qs(parts.query)
            targets = params.get("q") or params.get("url")
            if targets:
                return targets[0]
        return url

    @staticmethod
    def _strip_url_decorations(url: str) -> str:
        url = url.strip()
        for prefix in ("mailto:", "tel:", "https://", "http://"):
            if url.lower().startswith(prefix):
                url = url[len(prefix) :]
                break
        if url.lower().startswith("www."):
            url = url[4:]
        return url.rstrip("/")


class _HTMLTextExtractor(HTMLParser):
    """Collects the text content of an HTML fragment, dropping all tags.

    ``<br>`` (in any form: ``<br>``, ``<br/>``, ``<BR />``) becomes ``\\r\\n``.
    ``<a href="url">text</a>`` is handed to ``_Link``, which decides how the
    link reads as plain text (normally ``text (url)``).
    Character references (``&amp;``, ``&#39;``, ...) are decoded by the parser
    itself, so escaped markup such as ``&lt;b&gt;`` survives as literal text.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        # href of the <a> we are inside, and the text collected inside it so far
        self._open_link: str | None = None
        self._link_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "br":
            self._append("\r\n")
        elif tag == "a":
            self._close_link()
            href = (dict(attrs).get("href") or "").strip()
            if href:
                self._open_link = href

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            self._close_link()

    def handle_data(self, data: str) -> None:
        self._append(data)

    def _append(self, text: str) -> None:
        if self._open_link is not None:
            self._link_parts.append(text)
        else:
            self._parts.append(text)

    def _close_link(self) -> None:
        """Hand the open link and its collected text to ``_Link``."""
        if self._open_link is None:
            return
        link = _Link(self._open_link, "".join(self._link_parts))
        self._open_link = None
        self._link_parts = []
        self._parts.append(link.to_text())

    def get_text(self) -> str:
        self._close_link()
        return "".join(self._parts)


def unescape_text(s: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(s)
    parser.close()
    return parser.get_text()
