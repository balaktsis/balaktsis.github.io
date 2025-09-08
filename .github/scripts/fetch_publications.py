#!/usr/bin/env python3
import json
import os
import sys
import time
import random
from scholarly import scholarly, ProxyGenerator
import requests.exceptions

# Your Google Scholar ID
SCHOLAR_ID = "SC5NdrAAAAAJ"

# Maximum number of retries
MAX_RETRIES = 3
# Timeout for requests (in seconds)
TIMEOUT = 30
# Delay between requests (in seconds)
DELAY = 2

def setup_proxy():
    """Set up a proxy to avoid being blocked by Google Scholar"""
    pg = ProxyGenerator()
    # Try to use FreeProxy
    success = pg.FreeProxies()
    if success:
        scholarly.use_proxy(pg)
        print("Using FreeProxy")
    else:
        # Try Tor as a fallback if available
        try:
            success = pg.Tor_External(tor_sock_port=9050, tor_control_port=9051)
            if success:
                scholarly.use_proxy(pg)
                print("Using Tor proxy")
        except:
            print("Warning: Failed to set up proxy. May encounter rate limits.")

def fetch_publications_with_fallback():
    """Try to fetch publications from Google Scholar with retry logic"""
    
    # First try to use the scholarly library with retry logic
    for attempt in range(MAX_RETRIES):
        try:
            # Set up proxy
            setup_proxy()
            
            print(f"Attempt {attempt+1}/{MAX_RETRIES} to fetch publications")
            
            # Get author data
            author = scholarly.search_author_id(SCHOLAR_ID)
            scholarly.fill(author, sections=['publications'])
            
            # Extract publication information
            publications = []
            for i, pub in enumerate(author['publications']):
                try:
                    print(f"Processing publication {i+1}/{len(author['publications'])}")
                    scholarly.fill(pub)
                    publications.append({
                        'title': pub.get('bib', {}).get('title', ''),
                        'authors': pub.get('bib', {}).get('author', ''),
                        'venue': pub.get('bib', {}).get('journal', '') or pub.get('bib', {}).get('venue', ''),
                        'year': pub.get('bib', {}).get('pub_year', ''),
                        'link': pub.get('pub_url', '')
                    })
                    
                    # Add random delay between requests
                    time.sleep(DELAY + random.uniform(0, 1))
                except Exception as e:
                    print(f"Error processing publication: {e}")
                    continue
            
            # If we got publications, return them
            if publications:
                return publications
            
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        
        # Wait before retrying
        wait_time = (attempt + 1) * 5
        print(f"Waiting {wait_time} seconds before retry...")
        time.sleep(wait_time)
    
    # If all attempts failed, use the fallback data
    print("Failed to fetch from Google Scholar. Using fallback data.")
    return use_fallback_data()

def use_fallback_data():
    """Return hardcoded publication data as fallback"""
    return [
        {
            'title': 'Determination of activity duration in business process mining',
            'authors': 'Christos Balaktsis',
            'venue': 'Bachelor\'s Thesis, Aristotle University of Thessaloniki',
            'year': '2024',
            'link': 'https://ikee.lib.auth.gr/record/358500'
        }
    ]

def main():
    try:
        # Try to fetch publications
        publications = fetch_publications_with_fallback()
        
        # Check if we have existing file to preserve structure
        existing_data = {'publications': []}
        if os.path.exists('publications.json'):
            try:
                with open('publications.json', 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except json.JSONDecodeError:
                print("Warning: Existing publications.json is invalid. Creating new file.")
        
        # Save to publications.json
        with open('publications.json', 'w', encoding='utf-8') as f:
            json.dump({'publications': publications}, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(publications)} publications to publications.json")
        return True
    except Exception as e:
        print(f"Fatal error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)