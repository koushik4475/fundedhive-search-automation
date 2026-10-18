# FundedHive Search Automation [![Views](https://komarev.com/ghpvc/?username=Project121-ui&repo=fundedhive-search-automation&color=blue&style=flat-square)](https://github.com/Project121-ui/fundedhive-search-automation)

Automates parallel searches across multiple search engines for "FundedHive 1-minute payout" and correlated indexation verification, with dedicated X/Twitter post parsing.


## Features
- **Parallel Searching**: Fast multi-engine indexation checking (Google, Brave, DuckDuckGo, Yahoo, Bing, Yandex, Ecosia).
- **X Post Crawler**: Automatically visits the target X post to capture the tweet context and take a screenshot.
- **Aesthetic HTML Report**: Generates a interactive, premium dark-theme HTML report with screenshots and indexation status.
- **CSV Data Export**: Logs search URLs, titles, status, and screenshot paths in CSV format.

## Directory Structure
```text
fundedhive-search-automation/
├── main.py
├── engines.py
├── requirements.txt
├── README.md
├── .gitignore
└── results/               # Auto-created on run
    ├── report.html        # Beautiful indexation report
    ├── screenshots/       # Screenshots for searches & X post
    └── fundedhive_search_[timestamp].csv
```

## Installation
1. Ensure Chrome is installed on your system.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run with default query and target X post:
```bash
python main.py
```

Or customize query and target post:
```bash
python main.py --query "FundedHive compensation review" --x-post "https://x.com/HyKoushik63455/status/2060435122684629268?s=20"
```
