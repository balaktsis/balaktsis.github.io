#!/usr/bin/env python3
import json
import os
import time
import sys
from scholarly import scholarly
import random
from functools import wraps
from typing import Optional, Any
import signal
import unicodedata

# Ensure output is flushed immediately
sys.stdout.reconfigure(line_buffering=True)

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    print("TIMEOUT: Operation timed out!")
    sys.stdout.flush()
    raise TimeoutError("Operation timed out")

def with_timeout(seconds: int):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f"Setting timeout for {seconds} seconds...")
            sys.stdout.flush()
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
                print(f"Operation completed within {seconds} seconds")
                sys.stdout.flush()
            finally:
                signal.alarm(0)
            return result
        return wrapper
    return decorator

# Default publications that should always be included
DEFAULT_PUBLICATIONS = [{
    "title": "Determination of activity duration in business process mining",
    "authors": "Christos Balaktsis",
    "venue": "Bachelor Thesis, Aristotle University of Thessaloniki",
    "year": 2024,
    "link": "https://ikee.lib.auth.gr/record/358500"
}]

def contains_greek(text: str) -> bool:
    """Check if the text contains any Greek characters."""
    for char in text:
        if unicodedata.name(char, '').startswith('GREEK'):
            return True
    return False

# Your Google Scholar ID
SCHOLAR_ID = "SC5NdrAAAAAJ"




@with_timeout(180)  # 3-minute timeout for the entire operation
def fetch_publications():
    publications = []
    print("=== STARTING FETCH PUBLICATIONS ===")
    sys.stdout.flush()
    
    # Always ensure we save the default publications no matter what
    print("Ensuring default publications are available...")
    with open('publications.json', 'w', encoding='utf-8') as f:
        json.dump({'publications': DEFAULT_PUBLICATIONS}, f, ensure_ascii=False, indent=2)
    print("Default publications saved successfully")
    sys.stdout.flush()
    
    try:
        print("Attempting to fetch from Google Scholar...")
        sys.stdout.flush()
        
        # Get author data with retries
        print(f"Searching for author with ID: {SCHOLAR_ID}")
        sys.stdout.flush()
        author = scholarly.search_author_id(SCHOLAR_ID)
        if not author:
            raise ValueError(f"Could not find author with ID: {SCHOLAR_ID}")
            
        print("Found author, fetching publications...")
        sys.stdout.flush()
        if not author:
            raise ValueError(f"Could not find author with ID: {SCHOLAR_ID}")
            
        print("Found author, fetching publications...")
        scholarly.fill(author, sections=['publications'])
        
        if not author.get('publications'):
            raise ValueError("No publications found in author data")
                    
        new_publications = []
        for i, pub in enumerate(author['publications'], 1):
            try:
                print(f"Fetching details for publication {i}...")
                
                # Verify we have the basic publication data
                if not pub.get('bib'):
                    print(f"Warning: Publication {i} has no bibliographic data, skipping")
                    continue

                # Add timeout to each publication fetch
                with_timeout(30)(scholarly.fill)(pub)    
                # Get venue with better fallbacks
                bib = pub.get('bib', {})
                # For conference papers, prioritize conference name over publisher
                venue = (bib.get('journal', '') or 
                        bib.get('conference', '') or  # Add conference field
                        bib.get('citation', '') or
                        bib.get('booktitle', '') or  # Add booktitle field which often contains conference name
                        bib.get('venue', '') or 
                        bib.get('book', '') or
                        bib.get('container', '') or  # Add container field
                        bib.get('publisher', ''))
                
                if venue:
                    venue = venue.replace('\n', ' ').strip().split(',')[0]
                
                # Format authors by replacing 'and' with commas
                authors = bib.get('author', '')
                if authors:
                    authors = authors.replace(' and ', ', ')
                
                pub_data = {
                    'title': bib.get('title', ''),
                    'authors': authors,
                    'venue': venue,
                    'year': bib.get('pub_year', ''),
                    'link': pub.get('pub_url', '')
                }
                
                # Only add publications that have a title and are not in Greek
                if pub_data['title']:
                    if contains_greek(pub_data['title']):
                        print(f"Skipping publication {i} as it contains Greek characters: {pub_data['title'][:50]}...")
                    else:
                        new_publications.append(pub_data)
                        print(f"Successfully processed publication: {pub_data['title'][:50]}...")
                else:
                    print(f"Warning: Publication {i} has no title, skipping")
            except (TimeoutError, Exception) as e:
                print(f"Warning: Failed to fetch publication {i} details: {str(e)}")
                continue
        
        # Start with default publications
        final_publications = DEFAULT_PUBLICATIONS.copy()
        
        # Add any new publications that aren't in the defaults
        default_titles = {pub['title'] for pub in DEFAULT_PUBLICATIONS}
        for pub in new_publications:
            if pub['title'] not in default_titles:
                final_publications.append(pub)
        
        # Always save the combined publications
        with open('publications.json', 'w', encoding='utf-8') as f:
            json.dump({'publications': final_publications}, f, ensure_ascii=False, indent=2)
        print(f"Successfully saved {len(final_publications)} publications "
              f"({len(DEFAULT_PUBLICATIONS)} default + {len(final_publications) - len(DEFAULT_PUBLICATIONS)} fetched)")
            
    except TimeoutError:
        print("Operation timed out. Saving default publications.")
        with open('publications.json', 'w', encoding='utf-8') as f:
            json.dump({'publications': DEFAULT_PUBLICATIONS}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error fetching from Google Scholar: {str(e)}")
        print("Saving default publications.")
        with open('publications.json', 'w', encoding='utf-8') as f:
            json.dump({'publications': DEFAULT_PUBLICATIONS}, f, ensure_ascii=False, indent=2)
    
    print(f"Final publication count complete.")
    sys.stdout.flush()

if __name__ == "__main__":
    print("Starting publication fetch script...")
    sys.stdout.flush()
    try: 
        fetch_publications()
        print("Script completed successfully!")
        sys.stdout.flush()
    except Exception as e:
        print(f"Fatal error during fetch: {str(e)}")
        print("Saving default publications as fallback...")
        sys.stdout.flush()
        try:
            with open('publications.json', 'w', encoding='utf-8') as f:
                json.dump({'publications': DEFAULT_PUBLICATIONS}, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(DEFAULT_PUBLICATIONS)} default publications")
            sys.stdout.flush()
        except Exception as save_error:
            print(f"Error saving default publications: {str(save_error)}")
            sys.stdout.flush()
            exit(1)