# paper_search_mcp/sources/arxiv.py

from typing import List
from datetime import datetime
import requests
import feedparser
from paper import Paper
from PyPDF2 import PdfReader
from io import BytesIO


class PaperSource:
    """Abstract base class for paper sources"""
    def search(self, query: str, **kwargs) -> List[Paper]:
        raise NotImplementedError

    def download_pdf(self, paper_id: str, save_path: str) -> str:
        raise NotImplementedError

    def read_paper(self, paper_id: str) -> str:
        raise NotImplementedError


class ArxivSearcher(PaperSource):
    """Searcher for arXiv papers"""
    BASE_URL = "http://export.arxiv.org/api/query"

    def search(self, query: str, max_results: int = 10) -> List[Paper]:
        params = {
            'search_query': query,
            'max_results': max_results,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }

        response = requests.get(self.BASE_URL, params=params)
        feed = feedparser.parse(response.content)

        papers = []
        for entry in feed.entries:
            try:
                authors = [author.name for author in entry.authors]
                published = datetime.strptime(entry.published, '%Y-%m-%dT%H:%M:%SZ')
                updated = datetime.strptime(entry.updated, '%Y-%m-%dT%H:%M:%SZ')

                pdf_url = next(
                    (link.href for link in entry.links
                     if link.type == 'application/pdf'),
                    ''
                )

                papers.append(Paper(
                    paper_id=entry.id.split('/')[-1],
                    title=entry.title,
                    authors=authors,
                    abstract=entry.summary,
                    url=entry.id,
                    pdf_url=pdf_url,
                    published_date=published,
                    updated_date=updated,
                    source='arxiv',
                    categories=[tag.term for tag in entry.tags],
                    keywords=[],
                    doi=entry.get('doi', '')
                ))

            except Exception as e:
                print(f"Error parsing arXiv entry: {e}")

        return papers

    def read_paper(self, paper_id: str) -> str:
        """
        Read an arXiv paper entirely in memory without downloading the PDF to disk.

        Args:
            paper_id: e.g., '2107.12345'
        Returns:
            Extracted text content
        """
        pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"

        try:
            # Fetch PDF
            response = requests.get(pdf_url)
            response.raise_for_status()

            pdf_bytes = BytesIO(response.content)
            reader = PdfReader(pdf_bytes)

            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

            return text.strip()

        except Exception as e:
            print(f"Error reading PDF for paper {paper_id}: {e}")
            return ""


if __name__ == "__main__":
    # Test ArxivSearcher functionality
    searcher = ArxivSearcher()

    print("Testing search functionality...")
    query = "machine learning"
    max_results = 5

    try:
        papers = searcher.search(query, max_results=max_results)
        print(f"Found {len(papers)} papers for query '{query}':")
        for i, paper in enumerate(papers, 1):
            print(f"{i}. {paper.title} (ID: {paper.paper_id})")
    except Exception as e:
        print(f"Error during search: {e}")

    # Test paper reading functionality (in-memory only)
    if papers:
        print("\nTesting in-memory PDF reading...")
        paper_id = papers[0].paper_id

        try:
            text_content = searcher.read_paper(paper_id)
            print("\nFirst 500 characters of the paper content:")
            print(text_content[:5000] + "...")
            print(f"\nTotal length of extracted text: {len(text_content)} characters")
        except Exception as e:
            print(f"Error during paper reading: {e}")
