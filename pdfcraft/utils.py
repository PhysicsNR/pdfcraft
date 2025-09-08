
from __future__ import annotations
from typing import List, Tuple

def parse_page_ranges(spec: str, num_pages: int) -> List[int]:
    """
    Parse page range string like "1-3,5,8-" (1-based) into zero-based indices.
    A trailing "-" means to the end. Returns sorted unique indices.
    """
    pages = set()
    parts = [p.strip() for p in spec.split(",") if p.strip()]
    for part in parts:
        if "-" in part:
            a, b = part.split("-", 1)
            start = int(a) if a else 1
            end = int(b) if b else num_pages
            for p in range(start, end + 1):
                if 1 <= p <= num_pages:
                    pages.add(p - 1)
        else:
            p = int(part)
            if 1 <= p <= num_pages:
                pages.add(p - 1)
    return sorted(pages)

def clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(n, hi))
