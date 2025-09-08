#!/usr/bin/env python3
import json
import os
import time
from scholarly import scholarly, ProxyGenerator
import random
from functools import wraps
from typing import Optional, Any
import signal

# Your Google Scholar ID
SCHOLAR_ID = "SC5NdrAAAAAJ"

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def with_timeout(seconds: int):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Set the timeout handler
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                # Disable the alarm
                signal.alarm(0)
            return result
        return wrapper
    return decorator

def retry_with_backoff(retries: int = 3, backoff_in_seconds: int = 1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        raise e
                    sleep_time = (backoff_in_seconds * 2 ** x + 
                                random.uniform(0, 1))
                    time.sleep(sleep_time)
                    x += 1
        return wrapper
    return decorator

@retry_with_backoff(retries=3)
def setup_scholarly() -> bool:
    """Set up scholarly with custom settings to improve reliability"""
    try:
        # Use default settings without proxy to avoid compatibility issues
        scholarly.set_timeout(15)
        return True
    except Exception as e:
        print(f"Error setting up scholarly: {str(e)}")
        return False

@retry_with_backoff(retries=3)
@with_timeout(60)  # Set a 60-second timeout for the entire operation
def fetch_publications():
    publications = []
    try:
        # Try to load existing publications as fallback
        try:
            with open('publications.json', 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                publications = existing_data.get('publications', [])
                print(f"Loaded {len(publications)} publications from existing file as backup")
        except (FileNotFoundError, json.JSONDecodeError):
            print("No existing publications file found or file is invalid")
            pass

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
                with_timeout(10)(scholarly.fill)(pub)  # 10-second timeout per publication
                
                # Verify we have the basic publication data
                if not pub.get('bib'):
                    print(f"Warning: Publication {i} has no bibliographic data, skipping")
                    continue
                    
                # Get venue with fallbacks
                venue = (pub.get('bib', {}).get('journal', '') or 
                        pub.get('bib', {}).get('venue', '') or 
                        pub.get('bib', {}).get('book', '') or 
                        pub.get('bib', {}).get('publisher', ''))
                
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
                
                # Only add publications that have at least a title
                if pub_data['title']:
                    new_publications.append(pub_data)
                    print(f"Successfully processed publication: {pub_data['title'][:50]}...")
                else:
                    print(f"Warning: Publication {i} has no title, skipping")
            except (TimeoutError, Exception) as e:
                print(f"Warning: Failed to fetch publication {i} details: {str(e)}")
                continue
        
        # Update publications if we got new ones
        if new_publications:
            publications = new_publications
            with open('publications.json', 'w', encoding='utf-8') as f:
                json.dump({'publications': publications}, f, ensure_ascii=False, indent=2)
            print(f"Successfully fetched and saved {len(publications)} publications")
        else:
            print("No new publications found from Google Scholar, using existing data")
            
    except TimeoutError:
        print("Operation timed out. Using existing publications data.")
    except Exception as e:
        print(f"Error fetching from Google Scholar: {str(e)}")
        print("Using existing publications data as fallback")
    
    print(f"Final publication count: {len(publications)}")

if __name__ == "__main__":
    try:
        if setup_scholarly():
            fetch_publications()
        else:
            print("Failed to set up scholarly. Using existing publications data.")
            # Try to use existing data
            try:
                with open('publications.json', 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"Found {len(data.get('publications', []))} publications in existing data")
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(f"Error reading existing publications: {str(e)}")
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        exit(1)