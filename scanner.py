#!/usr/bin/env python3
"""
job-match-scanner: Scan Hacker News "Who's Hiring" threads for job matches.
Scores listings against Ian's skills and saves top results.
"""

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

import requests

KEYWORDS = ["data scientist", "ML engineer", "AI engineer", "machine learning", "deep learning"]

IAN_SKILLS = [
    "python", "fastapi", "react", "typescript", "xgboost", "yolov8", "nlp",
    "computer vision", "aws", "docker", "postgresql", "redis", "claude",
    "langchain", "scikit-learn", "pytorch", "tensorflow", "kubernetes",
    "sql", "git", "rest api", "microservices", "llm", "openai",
]

OUTPUT_DIR = Path.home() / ".job-scanner"
HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"


def fetch_hn_jobs(query: str, limit: int = 50) -> list[dict]:
    """Fetch HN comments from 'Who's Hiring' threads."""
    params = {
        "query": query,
        "tags": "comment",
        "hitsPerPage": limit,
    }
    try:
        resp = requests.get(HN_SEARCH_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("hits", [])
    except Exception as e:
        print(f"[warn] HN fetch failed for '{query}': {e}", file=sys.stderr)
        return []


def score_listing(text: str) -> tuple[int, list[str]]:
    """Score a job listing against Ian's skills. Returns (score, matched_skills)."""
    text_lower = text.lower()
    matched = []
    for skill in IAN_SKILLS:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            matched.append(skill)
    score = len(matched) * 10
    # Bonus for seniority indicators that fit Ian's level
    if any(w in text_lower for w in ["senior", "lead", "staff"]):
        score += 5
    if any(w in text_lower for w in ["junior", "intern", "entry"]):
        score -= 10
    # Bonus for remote
    if "remote" in text_lower:
        score += 5
    return max(0, score), matched


def clean_text(html: str) -> str:
    """Strip HTML tags."""
    clean = re.sub(r"<[^>]+>", " ", html or "")
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def build_hn_url(object_id: str) -> str:
    return f"https://news.ycombinator.com/item?id={object_id}"


def main():
    parser = argparse.ArgumentParser(description="Scan HN Who's Hiring for job matches.")
    parser.add_argument("--keywords", nargs="+", default=KEYWORDS, help="Keywords to search")
    parser.add_argument("--limit", type=int, default=50, help="Max results per keyword")
    parser.add_argument("--top", type=int, default=10, help="Number of top results to show")
    parser.add_argument("--no-save", action="store_true", help="Skip saving results to disk")
    args = parser.parse_args()

    print(f"Scanning HN for: {', '.join(args.keywords)}")
    print(f"Scoring against {len(IAN_SKILLS)} skills...\n")

    seen_ids = set()
    all_listings = []

    for keyword in args.keywords:
        hits = fetch_hn_jobs(keyword, limit=args.limit)
        for hit in hits:
            obj_id = hit.get("objectID", "")
            if obj_id in seen_ids:
                continue
            seen_ids.add(obj_id)
            raw = hit.get("comment_text") or hit.get("story_text") or ""
            text = clean_text(raw)
            if len(text) < 50:
                continue
            score, matched = score_listing(text)
            if score <= 0:
                continue
            all_listings.append({
                "id": obj_id,
                "score": score,
                "matched_skills": matched,
                "snippet": text[:300],
                "url": build_hn_url(obj_id),
                "author": hit.get("author", ""),
                "created_at": hit.get("created_at", ""),
            })

    # Deduplicate and sort
    all_listings.sort(key=lambda x: x["score"], reverse=True)
    top_results = all_listings[:args.top]

    if not top_results:
        print("No matches found. Try different keywords or check your connection.")
        return

    print(f"Top {len(top_results)} matches:\n")
    print(f"{'#':<4} {'Score':<8} {'Skills Matched':<40} {'URL'}")
    print("-" * 90)
    for i, listing in enumerate(top_results, 1):
        skills_str = ", ".join(listing["matched_skills"][:5])
        if len(listing["matched_skills"]) > 5:
            skills_str += f" +{len(listing['matched_skills']) - 5} more"
        print(f"{i:<4} {listing['score']:<8} {skills_str:<40} {listing['url']}")
        print(f"     {listing['snippet'][:120]}...")
        print()

    if not args.no_save:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        out_file = OUTPUT_DIR / f"results-{date.today().isoformat()}.json"
        out_file.write_text(json.dumps(top_results, indent=2))
        print(f"Saved to {out_file}")


if __name__ == "__main__":
    main()
