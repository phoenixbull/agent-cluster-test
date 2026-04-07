#!/usr/bin/env python3
"""
Tavily Search Script
Search the web using Tavily API
"""

import os
import sys
import json
import argparse
import requests

TAVILY_API_URL = "https://api.tavily.com/search"


def search_tavily(query, api_key=None, max_results=5, search_depth="basic", 
                  include_domains=None, exclude_domains=None, include_images=False):
    """
    Search using Tavily API
    
    Args:
        query: Search query string
        api_key: Tavily API key (or set TAVILY_API_KEY env var)
        max_results: Maximum number of results (default: 5)
        search_depth: "basic" or "advanced" (default: "basic")
        include_domains: List of domains to include
        exclude_domains: List of domains to exclude
        include_images: Include image URLs in results
    
    Returns:
        dict: Search results
    """
    api_key = api_key or os.environ.get("TAVILY_API_KEY")
    
    if not api_key:
        print("Error: TAVILY_API_KEY not set", file=sys.stderr)
        print("Please set your Tavily API key:", file=sys.stderr)
        print("  export TAVILY_API_KEY=your-key-here", file=sys.stderr)
        print("\nGet your API key from: https://app.tavily.com", file=sys.stderr)
        sys.exit(1)
    
    payload = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
        "include_answer": True,
        "include_raw_content": False,
        "include_images": include_images
    }
    
    if include_domains:
        payload["include_domains"] = include_domains
    
    if exclude_domains:
        payload["exclude_domains"] = exclude_domains
    
    try:
        response = requests.post(TAVILY_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: API request failed: {e}", file=sys.stderr)
        sys.exit(1)


def format_results(results, output_format="text"):
    """Format search results for display"""
    
    if output_format == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return
    
    # Text format
    if "answer" in results:
        print("🤖 AI Answer:")
        print(results["answer"])
        print("\n" + "="*60 + "\n")
    
    print(f"📊 Search Results ({len(results.get('results', []))} found):\n")
    
    for i, result in enumerate(results.get("results", []), 1):
        print(f"{i}. **{result.get('title', 'No title')}**")
        print(f"   URL: {result.get('url', 'N/A')}")
        print(f"   {result.get('content', 'No description')}")
        
        if "score" in result:
            print(f"   Relevance: {result['score']:.2f}")
        
        if "published_date" in result:
            print(f"   Published: {result['published_date']}")
        
        if result.get("image"):
            print(f"   Image: {result['image']}")
        
        print()


def main():
    parser = argparse.ArgumentParser(description="Search the web using Tavily API")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--api-key", help="Tavily API key (or set TAVILY_API_KEY env var)")
    parser.add_argument("-n", "--max-results", type=int, default=5, 
                        help="Maximum number of results (default: 5)")
    parser.add_argument("--search-depth", choices=["basic", "advanced"], default="basic",
                        help="Search depth (default: basic)")
    parser.add_argument("--include-domains", nargs="+", help="Specific domains to include")
    parser.add_argument("--exclude-domains", nargs="+", help="Domains to exclude")
    parser.add_argument("--include-images", action="store_true", help="Include image URLs")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format (default: text)")
    
    args = parser.parse_args()
    
    results = search_tavily(
        query=args.query,
        api_key=args.api_key,
        max_results=args.max_results,
        search_depth=args.search_depth,
        include_domains=args.include_domains,
        exclude_domains=args.exclude_domains,
        include_images=args.include_images
    )
    
    format_results(results, args.format)


if __name__ == "__main__":
    main()
