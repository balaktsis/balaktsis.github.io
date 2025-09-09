#!/usr/bin/env python3
import json
import os
import time
from scholarly import scholarly
import random
from functools import wraps
from typing import Optional, Any
import signal
import unicodedata

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

def fetch_publications():
    publications = []
    print("Fetching data for author")
    try:
        # Try to load existing publications as fallback
        try:
            with open('publications.json', 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                publications = existing_data.get('publications', [])
                print(f"Loaded {len(publications)} publications from existing file as backup")
        except (FileNotFoundError, json.JSONDecodeError):
            print("No existing publications file found or file is invalid")

        # Get author data with retries
        print(f"Searching for author with ID: {SCHOLAR_ID}")
        author = scholarly.search_author_id(SCHOLAR_ID)
        if not author:
            raise ValueError(f"Could not find author with ID: {SCHOLAR_ID}")
            
        print("Found author, fetching publications...")
        scholarly.fill(author, sections=['publications'])
        
        if not author.get('publications'):
            raise ValueError("No publications found in author data")
            
        # Extract publication information
        new_publications = []
        print(f"Processing {len(author['publications'])} publications...")
        for i, pub in enumerate(author['publications'], 1):
            try:
                print(f"Fetching details for publication {i}...")
                
                # Verify we have the basic publication data
                if not pub.get('bib'):
                    print(f"Warning: Publication {i} has no bibliographic data, skipping")
                    continue
                    
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
                
                # Format authors by replacing 'and' with commas
                authors = pub.get('bib', {}).get('author', '')
                if authors:
                    authors = authors.replace(' and ', ', ')
                
                pub_data = {
                    'title': pub.get('bib', {}).get('title', ''),
                    'authors': authors,
                    'venue': venue,
                    'year': pub.get('bib', {}).get('pub_year', ''),
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
    
    print(f"Final publication count: {len(publications)}")

if __name__ == "__main__":
    try: 
        fetch_publications()
    except:
            print("Failed to set up scholarly. Using existing publications data.")
            try:
                with open('publications.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"Found {len(data.get('publications', []))} publications in existing data")
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error reading existing publications: {str(e)}")
                exit(1)
