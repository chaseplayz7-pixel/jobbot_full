"""Lightweight helper functions used by tests and scrapers.
This keeps small parsing utilities independent from heavy imports in `scraper.py`.
"""

from typing import Tuple, List


def detect_visa_signals(text: str) -> Tuple[List[str], int]:
    VISA_KEYWORDS = [
        'global talent stream',
        'gts',
        'lmia',
        'visa sponsorship',
        'work permit',
    ]
    text_l = (text or '').lower()
    hits = [k for k in VISA_KEYWORDS if k in text_l]
    return hits, len(hits)


def normalize_location(raw: str):
    if not raw:
        return '', ''
    parts = [p.strip() for p in raw.split(',') if p.strip()]
    if len(parts) == 1:
        return parts[0], ''
    return parts[0], parts[-1]


def filter_by_keywords(entry: dict, keywords):
    txt = (entry.get('title','') + ' ' + entry.get('description','') + ' ' + entry.get('company','')).lower()
    for k in keywords:
        if k.lower() in txt:
            return True
    return False
