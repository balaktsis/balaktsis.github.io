#!/usr/bin/env python3
import json
import os
import time
from scholarly import scholarly, ProxyGenerator

# Your Google Scholar ID
SCHOLAR_ID = "SC5NdrAAAAAJ"

def setup_scholarly():
    """Set up scholarly with custom settings to improve reliability"""
    try:
        # Set up a proxy generator
        pg = ProxyGenerator()
        success = pg.FreeProxies()
        scholarly.use_proxy(pg)
        
        # Set up fake browser headers
        scholarly.set_timeout(30)
        return True
    except Exception as e:
        print(f"Error setting up scholarly: {str(e)}")
        return False

def fetch_publications():
    try:
        # Get author data
        author = scholarly.search_author_id(SCHOLAR_ID)
        scholarly.fill(author, sections=['publications'])
        
        # Extract publication information
        publications = []
        for pub in author['publications']:
            scholarly.fill(pub)
            # Get venue with fallbacks
            venue = (pub.get('bib', {}).get('journal', '') or 
                    pub.get('bib', {}).get('venue', '') or 
                    pub.get('bib', {}).get('book', '') or 
                    pub.get('bib', {}).get('publisher', ''))
            
            # Format authors by replacing 'and' with commas
            authors = pub.get('bib', {}).get('author', '')
            authors = authors.replace(' and ', ', ')
            
            publications.append({
                'title': pub.get('bib', {}).get('title', ''),
                'authors': authors,
                'venue': venue,
                'year': pub.get('bib', {}).get('pub_year', ''),
                'link': pub.get('pub_url', '')
            })
        
        # Save to publications.json only if we successfully got publications
        if publications:
            with open('publications.json', 'w', encoding='utf-8') as f:
                json.dump({'publications': publications}, f, ensure_ascii=False, indent=2)
            print(f"Successfully fetched and saved {len(publications)} publications")
        else:
            print("No publications found from Google Scholar")
            
    except Exception as e:
        print(f"Error fetching from Google Scholar: {str(e)}")
        print("Using existing publications.json as fallback")
    
    print(f"Saved {len(publications)} publications to publications.json")

if __name__ == "__main__":
    if setup_scholarly():
        fetch_publications()