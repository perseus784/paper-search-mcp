from typing import List, Dict
import httpx
from academic_platforms.arxiv import ArxivSearcher
from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("paper_search_server")

# Only keep arXiv
arxiv_searcher = ArxivSearcher()


# Async adapter for the sync arxiv searcher
async def async_search_arxiv(query: str, max_results: int) -> List[Dict]:
    async with httpx.AsyncClient():
        papers = arxiv_searcher.search(query, max_results=max_results)
        return [paper.to_dict() for paper in papers]


# --- TOOLS --------------------------------------------------------

@mcp.tool()
async def search_arxiv(query: str, max_results: int = 10) -> List[Dict]:
    """
    Search academic papers on arXiv.
    """
    papers = await async_search_arxiv(query, max_results)
    return papers if papers else []


@mcp.tool()
async def read_arxiv_paper(paper_id: str) -> str:
    """
    Extract text from an arXiv PDF.
    """
    try:
        return arxiv_searcher.read_paper(paper_id)
    except Exception as e:
        print(f"Error reading paper {paper_id}: {e}")
        return ""


# Entry point
if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
