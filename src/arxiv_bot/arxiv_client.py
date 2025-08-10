"""
ArXiv API client for fetching research papers
Handles searching, filtering, and downloading papers from ArXiv

Author: Sreeram Lagisetty
Email: sreeram.lagisetty@gmail.com
GitHub: https://github.com/Sreeram5678
"""

import arxiv
import requests
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
import logging
from pathlib import Path


@dataclass
class Paper:
    """Represents an ArXiv paper"""
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    published: datetime
    updated: datetime
    arxiv_id: str
    pdf_url: str
    entry_id: str
    summary: Optional[str] = None
    
    def __post_init__(self):
        """Clean up title and abstract"""
        self.title = self._clean_text(self.title)
        self.abstract = self._clean_text(self.abstract)
    
    def _clean_text(self, text: str) -> str:
        """Clean up text by removing extra whitespace and line breaks"""
        # Remove extra whitespace and normalize line breaks
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove common LaTeX commands
        text = re.sub(r'\$[^$]*\$', '', text)  # Remove math expressions
        text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)  # Remove LaTeX commands
        return text.strip()
    
    def matches_keywords(self, keywords: List[str]) -> bool:
        """Check if paper matches any of the provided keywords"""
        if not keywords:
            return True
        
        text_to_search = f"{self.title} {self.abstract}".lower()
        return any(keyword.lower() in text_to_search for keyword in keywords)
    
    def to_dict(self) -> Dict:
        """Convert paper to dictionary format"""
        return {
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'categories': self.categories,
            'published': self.published.isoformat(),
            'updated': self.updated.isoformat(),
            'arxiv_id': self.arxiv_id,
            'pdf_url': self.pdf_url,
            'entry_id': self.entry_id,
            'summary': self.summary
        }


class ArxivClient:
    """Client for interacting with ArXiv API"""
    
    def __init__(self, max_results_per_query: int = 100):
        self.max_results_per_query = max_results_per_query
        self.logger = logging.getLogger(__name__)
    
    def search_papers(
        self,
        categories: List[str],
        keywords: List[str] = None,
        days_back: int = 1,
        max_papers: int = 50
    ) -> List[Paper]:
        """
        Search for papers in specified categories and filter by keywords
        """
        self.logger.info(f"Searching papers in categories: {categories}")
        self.logger.info(f"Keywords: {keywords}")
        self.logger.info(f"Looking back {days_back} days")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        all_papers = []
        
        for category in categories:
            try:
                papers = self._search_category(
                    category=category,
                    start_date=start_date,
                    end_date=end_date,
                    max_results=self.max_results_per_query
                )
                all_papers.extend(papers)
                self.logger.info(f"Found {len(papers)} papers in category {category}")
                
            except Exception as e:
                self.logger.error(f"Error searching category {category}: {e}")
                continue
        
        # Remove duplicates based on ArXiv ID
        unique_papers = {}
        for paper in all_papers:
            if paper.arxiv_id not in unique_papers:
                unique_papers[paper.arxiv_id] = paper
        
        papers_list = list(unique_papers.values())
        
        # Filter by keywords if provided
        if keywords:
            papers_list = [p for p in papers_list if p.matches_keywords(keywords)]
            self.logger.info(f"After keyword filtering: {len(papers_list)} papers")
        
        # Sort by publication date (newest first)
        papers_list.sort(key=lambda p: p.published, reverse=True)
        
        # Limit to max_papers
        if len(papers_list) > max_papers:
            papers_list = papers_list[:max_papers]
            self.logger.info(f"Limited to {max_papers} papers")
        
        self.logger.info(f"Final result: {len(papers_list)} papers")
        return papers_list
    
    def _search_category(
        self,
        category: str,
        start_date: datetime,
        end_date: datetime,
        max_results: int = 100
    ) -> List[Paper]:
        """Search papers in a specific category within date range"""
        
        # Build search query
        # ArXiv date format: YYYYMMDD
        start_date_str = start_date.strftime("%Y%m%d")
        end_date_str = end_date.strftime("%Y%m%d")
        
        # Create search query for category and date range
        search_query = f"cat:{category} AND submittedDate:[{start_date_str} TO {end_date_str}]"
        
        try:
            # Create search
            search = arxiv.Search(
                query=search_query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            papers = []
            for result in search.results():
                try:
                    paper = self._result_to_paper(result)
                    
                    # Additional date filtering (ArXiv search can be imprecise)
                    if start_date <= paper.published <= end_date:
                        papers.append(paper)
                        
                except Exception as e:
                    self.logger.warning(f"Error processing paper {result.entry_id}: {e}")
                    continue
            
            return papers
            
        except Exception as e:
            self.logger.error(f"Error in ArXiv search for category {category}: {e}")
            return []
    
    def _result_to_paper(self, result) -> Paper:
        """Convert ArXiv search result to Paper object"""
        return Paper(
            title=result.title,
            authors=[str(author) for author in result.authors],
            abstract=result.summary,
            categories=result.categories,
            published=result.published,
            updated=result.updated,
            arxiv_id=result.get_short_id(),
            pdf_url=result.pdf_url,
            entry_id=result.entry_id
        )
