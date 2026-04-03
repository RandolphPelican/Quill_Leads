from typing import List
from bs4 import BeautifulSoup
from .base import BaseCrawler, RawLead

class IndustrialNewsCrawler(BaseCrawler):
    async def parse(self, html: str, url: str) -> RawLead:
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        clean_text = " ".join(soup.get_text(separator=' ').split())
        return RawLead(
            source_url=url,
            raw_content=clean_text,
            metadata={"title": soup.title.string if soup.title else "Untitled"}
        )

    async def run(self, target_list: List[str]) -> List[RawLead]:
        leads = []
        for url in target_list:
            html = await self.fetch(url)
            if html:
                leads.append(await self.parse(html, url))
        return leads
