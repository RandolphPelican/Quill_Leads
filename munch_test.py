import asyncio
import sys
import os

# This ensures Python can see the 'agents' folder
sys.path.append(os.getcwd())

from agents.scraper_agent.news_crawler import IndustrialNewsCrawler
from agents.scraper_agent.entity_extractor import EntityExtractor

async def run_test():
    crawler = IndustrialNewsCrawler()
    extractor = EntityExtractor()
    
    # Testing a site likely to have industrial project news
    target_urls = ["https://www.power-eng.com/news/"]
    
    print(f"--- 🕸️  Munching {target_urls[0]} ---")
    
    try:
        results = await crawler.run(target_urls)
        
        for lead in results:
            company = extractor.get_best_guess_company(lead)
            print(f"\n✅ Target Identified: {company}")
            print(f"📄 Data Snippet: {lead.raw_content[:150]}...")
            
    except Exception as e:
        print(f"❌ Error during munching: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
