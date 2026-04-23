from __future__ import annotations

import requests
from bs4 import BeautifulSoup

from app.models import InputDocument


class UrlLoader:
    def __init__(self, timeout_seconds: int = 20) -> None:
        self.timeout_seconds = timeout_seconds

    def load(self, url: str) -> InputDocument:
        response = requests.get(
            url,
            timeout=self.timeout_seconds,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; Assignment2Bot/1.0)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            tag.decompose()

        text = " ".join(soup.stripped_strings)
        return InputDocument(
            source_type="url",
            source_name=url,
            source_id=url,
            raw_text=text,
        )
