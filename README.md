# job-match-scanner

Scans Hacker News "Who's Hiring" threads for job listings that match Ian's skills.
Scores each listing and outputs a ranked top 10. Saves results as JSON.

## Skills it matches against

Python, FastAPI, React, TypeScript, XGBoost, YOLOv8, NLP, Computer Vision, AWS, Docker, PostgreSQL, Redis, Claude API

## Install

```bash
pip3 install --break-system-packages requests
```

## Run

```bash
python3 scanner.py
```

Options:

```
--keywords KEYWORD [...]   Keywords to search (default: data scientist, ML engineer, AI engineer)
--limit N                  Max results per keyword (default: 50)
--top N                    Number of top results to show (default: 10)
--no-save                  Skip saving results to disk
--help                     Show help
```

## Output

Results saved to `~/.job-scanner/results-YYYY-MM-DD.json`.

Each result includes: score, matched skills, snippet, and HN URL.
