import httpx
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pydantic import BaseModel

class RawLead(BaseModel):
    source_url: str
    raw_content: str
    metadata: Dict[str, Any]

class BaseCrawler(ABC):
    def __init__(self, user_agent: str = "Quill_Leads_Bot/1.0"):
        self.headers = {"User-Agent": user_agent}

    async def fetch(self, url: str) -> str:
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
            try:
                response = await client.get(url, timeout=15.0)
                response.raise_for_status()
                return response.text
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                return ""

    @abstractmethod
    async def run(self, target_list: List[str]) -> List[RawLead]:
        pass
