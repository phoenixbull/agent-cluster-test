---
name: tavily-search
description: Search the web using Tavily API for fast, accurate search results with AI-friendly formatting.
author: OpenClaw Community
version: 1.0.0
homepage: https://tavily.com
triggers:
  - "search for"
  - "search web"
  - "find information"
  - "look up"
  - "tavily search"
metadata: {"clawdbot":{"emoji":"🔍","requires":{"env":{"TAVILY_API_KEY":{"description":"Tavily API key","required":true}}}}}
---

# Tavily Search

Search the web using Tavily API - optimized for AI agents with clean, structured results.

## Setup

1. Get your API key from https://app.tavily.com
2. Set environment variable: `export TAVILY_API_KEY=your-key-here`
3. Or add to your Gateway config

## Commands

### Basic Search
```bash
python3 {baseDir}/scripts/tavily_search.py "your query"
```

### Search with Options
```bash
python3 {baseDir}/scripts/tavily_search.py "query" --max-results 10
python3 {baseDir}/scripts/tavily_search.py "query" --search-depth advanced
python3 {baseDir}/scripts/tavily_search.py "query" --include-images
```

### JSON Output
```bash
python3 {baseDir}/scripts/tavily_search.py "query" --format json
```

## Examples

Search for latest AI news:
```bash
python3 {baseDir}/scripts/tavily_search.py "latest AI developments 2026"
```

Search with specific domain:
```bash
python3 {baseDir}/scripts/tavily_search.py "Python tutorials" --domains youtube.com
```

Get search results with images:
```bash
python3 {baseDir}/scripts/tavily_search.py "electric cars" --include-images
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `TAVILY_API_KEY` | - | Your Tavily API key (required) |
| `max_results` | 5 | Maximum number of results |
| `search_depth` | basic | Search depth: basic or advanced |
| `include_domains` | [] | Specific domains to search |
| `exclude_domains` | [] | Domains to exclude |
| `include_images` | false | Include image URLs in results |

## API Reference

Tavily API provides:
- **title**: Result title
- **url**: Source URL
- **content**: Clean text excerpt
- **score**: Relevance score (0-1)
- **published_date**: Publication date (if available)
- **image**: Image URL (if requested)

---

**Note**: Tavily is optimized for AI agents with clean, structured results perfect for RAG and question answering.
