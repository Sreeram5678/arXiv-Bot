"""
Helper utilities for ArXiv Bot
Common functions and utilities used across the application
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
import re
import pickle
from urllib.parse import urlparse


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if it doesn't"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(filename: str, max_length: int = 100) -> str:
    """
    Convert string to safe filename
    
    Args:
        filename: Original filename
        max_length: Maximum length of filename
        
    Returns:
        Safe filename string
    """
    # Remove or replace invalid characters
    safe_chars = re.sub(r'[<>:"/\\|?*]', '_', filename)
    safe_chars = re.sub(r'\s+', '_', safe_chars)
    safe_chars = re.sub(r'_{2,}', '_', safe_chars)
    
    # Remove leading/trailing underscores and dots
    safe_chars = safe_chars.strip('_.')
    
    # Truncate if too long
    if len(safe_chars) > max_length:
        safe_chars = safe_chars[:max_length].rstrip('_.')
    
    # Ensure it's not empty
    if not safe_chars:
        safe_chars = "unnamed"
    
    return safe_chars


def generate_file_hash(content: Union[str, bytes]) -> str:
    """Generate SHA-256 hash of content"""
    if isinstance(content, str):
        content = content.encode('utf-8')
    
    return hashlib.sha256(content).hexdigest()


def save_json(data: Any, filepath: Union[str, Path], indent: int = 2) -> bool:
    """
    Save data to JSON file
    
    Args:
        data: Data to save
        filepath: Path to save file
        indent: JSON indentation
        
    Returns:
        True if successful, False otherwise
    """
    try:
        filepath = Path(filepath)
        ensure_directory(filepath.parent)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
        
        return True
        
    except Exception:
        return False


def load_json(filepath: Union[str, Path]) -> Optional[Any]:
    """
    Load data from JSON file
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Loaded data or None if failed
    """
    try:
        filepath = Path(filepath)
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
        
    except Exception:
        return None


def save_pickle(data: Any, filepath: Union[str, Path]) -> bool:
    """
    Save data to pickle file
    
    Args:
        data: Data to save
        filepath: Path to save file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        filepath = Path(filepath)
        ensure_directory(filepath.parent)
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        
        return True
        
    except Exception:
        return False


def load_pickle(filepath: Union[str, Path]) -> Optional[Any]:
    """
    Load data from pickle file
    
    Args:
        filepath: Path to pickle file
        
    Returns:
        Loaded data or None if failed
    """
    try:
        filepath = Path(filepath)
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'rb') as f:
            return pickle.load(f)
        
    except Exception:
        return None


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def clean_html(text: str) -> str:
    """Remove HTML tags from text"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def extract_arxiv_id(url_or_text: str) -> Optional[str]:
    """
    Extract ArXiv ID from URL or text
    
    Args:
        url_or_text: URL or text containing ArXiv ID
        
    Returns:
        ArXiv ID or None if not found
    """
    # Pattern for ArXiv IDs (both old and new formats)
    patterns = [
        r'(?:arxiv:|arXiv:|https?://arxiv\.org/abs/)?(\d{4}\.\d{4,5}(?:v\d+)?)',
        r'(?:arxiv:|arXiv:|https?://arxiv\.org/abs/)?([a-z-]+(?:\.[A-Z]{2})?/\d{7}(?:v\d+)?)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_text)
        if match:
            return match.group(1)
    
    return None


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def validate_email(email: str) -> bool:
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_url(url: str) -> bool:
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def get_file_age(filepath: Union[str, Path]) -> Optional[timedelta]:
    """
    Get age of file
    
    Args:
        filepath: Path to file
        
    Returns:
        File age as timedelta or None if file doesn't exist
    """
    try:
        filepath = Path(filepath)
        
        if not filepath.exists():
            return None
        
        modified_time = datetime.fromtimestamp(filepath.stat().st_mtime)
        return datetime.now() - modified_time
        
    except Exception:
        return None


def is_file_recent(filepath: Union[str, Path], max_age_hours: int = 24) -> bool:
    """
    Check if file is recent (modified within max_age_hours)
    
    Args:
        filepath: Path to file
        max_age_hours: Maximum age in hours
        
    Returns:
        True if file is recent, False otherwise
    """
    age = get_file_age(filepath)
    if age is None:
        return False
    
    return age < timedelta(hours=max_age_hours)


def batch_list(items: List[Any], batch_size: int) -> List[List[Any]]:
    """
    Split list into batches
    
    Args:
        items: List to split
        batch_size: Size of each batch
        
    Returns:
        List of batches
    """
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def deduplicate_papers(papers: List[Dict], key: str = 'arxiv_id') -> List[Dict]:
    """
    Remove duplicate papers based on a key
    
    Args:
        papers: List of paper dictionaries
        key: Key to use for deduplication
        
    Returns:
        List of unique papers
    """
    seen = set()
    unique_papers = []
    
    for paper in papers:
        identifier = paper.get(key)
        if identifier and identifier not in seen:
            seen.add(identifier)
            unique_papers.append(paper)
    
    return unique_papers


def merge_configs(base_config: Dict, override_config: Dict) -> Dict:
    """
    Merge two configuration dictionaries
    
    Args:
        base_config: Base configuration
        override_config: Configuration to override with
        
    Returns:
        Merged configuration
    """
    result = base_config.copy()
    
    for key, value in override_config.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result


def filter_papers_by_date(
    papers: List[Dict],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    date_field: str = 'published'
) -> List[Dict]:
    """
    Filter papers by date range
    
    Args:
        papers: List of paper dictionaries
        start_date: Start date filter
        end_date: End date filter
        date_field: Field to use for date filtering
        
    Returns:
        Filtered papers
    """
    if not start_date and not end_date:
        return papers
    
    filtered = []
    
    for paper in papers:
        paper_date_str = paper.get(date_field)
        if not paper_date_str:
            continue
        
        try:
            # Parse date string
            if isinstance(paper_date_str, str):
                paper_date = datetime.fromisoformat(paper_date_str.replace('Z', '+00:00'))
            elif isinstance(paper_date_str, datetime):
                paper_date = paper_date_str
            else:
                continue
            
            # Apply filters
            if start_date and paper_date < start_date:
                continue
            
            if end_date and paper_date > end_date:
                continue
            
            filtered.append(paper)
            
        except Exception:
            continue
    
    return filtered


def create_summary_statistics(papers: List[Dict], summaries: List[Dict]) -> Dict:
    """
    Create summary statistics for papers and summaries
    
    Args:
        papers: List of paper dictionaries
        summaries: List of summary dictionaries
        
    Returns:
        Statistics dictionary
    """
    # Count papers by category
    category_counts = {}
    for paper in papers:
        for category in paper.get('categories', []):
            category_counts[category] = category_counts.get(category, 0) + 1
    
    # Count papers by author (top 10)
    author_counts = {}
    for paper in papers:
        for author in paper.get('authors', []):
            author_counts[author] = author_counts.get(author, 0) + 1
    
    top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Summary statistics
    successful_summaries = sum(1 for s in summaries if s.get('summary'))
    avg_summary_length = 0
    if successful_summaries > 0:
        total_length = sum(len(s.get('summary', '')) for s in summaries if s.get('summary'))
        avg_summary_length = total_length / successful_summaries
    
    return {
        'total_papers': len(papers),
        'total_summaries': len(summaries),
        'successful_summaries': successful_summaries,
        'summary_success_rate': successful_summaries / len(summaries) if summaries else 0,
        'avg_summary_length': avg_summary_length,
        'category_distribution': category_counts,
        'top_authors': top_authors,
        'categories_count': len(category_counts),
        'unique_authors_count': len(author_counts)
    }
