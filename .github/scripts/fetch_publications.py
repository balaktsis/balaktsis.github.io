#!/usr/bin/env python3
import json
import os
from scholarly import scholarly

# Your Google Scholar ID
SCHOLAR_ID = "SC5NdrAAAAAJ"

def fetch_publications():
    # Get author data
    author = scholarly.search_author_id(SCHOLAR_ID)
    scholarly.fill(author, sections=['publications'])
    
    # Extract publication information
    publications = []
    for pub in author['publications']:
        scholarly.fill(pub)
        publications.append({
            'title': pub.get('bib', {}).get('title', ''),
            'authors': pub.get('bib', {}).get('author', ''),
            'venue': pub.get('bib', {}).get('journal', '') or pub.get('bib', {}).get('venue', ''),
            'year': pub.get('bib', {}).get('pub_year', ''),
            'link': pub.get('pub_url', '')
        })
    
    # Save to publications.json
    with open('publications.json', 'w', encoding='utf-8') as f:
        json.dump({'publications': publications}, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(publications)} publications to publications.json")

if __name__ == "__main__":
    fetch_publications()