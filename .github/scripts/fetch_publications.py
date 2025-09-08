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
        # Try different proxy methods
        pg = ProxyGenerator()
        proxy_success = False
        
        # Try different proxy methods in sequence
        if pg.FreeProxies():
            proxy_success = True
        elif pg.Tor_External(tor_sock_port=9050, tor_control_port=9051):
            proxy_success = True
        elif pg.ScraperAPI():
            proxy_success = True

        # Only use proxy if we successfully set one up
        if proxy_success:
            scholarly.use_proxy(pg)
        else:
            print("Warning: No proxy method succeeded, trying without proxy")
        
        # Set shorter timeout for operations
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
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Get author data
        author = scholarly.search_author_id(SCHOLAR_ID)
        scholarly.fill(author, sections=['publications'])
        
        # Extract publication information
        new_publications = []
        for pub in author['publications']:
            try:
                with_timeout(10)(scholarly.fill)(pub)  # 10-second timeout per publication
                # Get venue with fallbacks
                venue = (pub.get('bib', {}).get('journal', '') or 
                        pub.get('bib', {}).get('venue', '') or 
                        pub.get('bib', {}).get('book', '') or 
                        pub.get('bib', {}).get('publisher', ''))
                
                # Format authors by replacing 'and' with commas
                authors = pub.get('bib', {}).get('author', '')
                authors = authors.replace(' and ', ', ')
                
                new_publications.append({
                    'title': pub.get('bib', {}).get('title', ''),
                    'authors': authors,
                    'venue': venue,
                    'year': pub.get('bib', {}).get('pub_year', ''),
                    'link': pub.get('pub_url', '')
                })
            except (TimeoutError, Exception) as e:
                print(f"Warning: Failed to fetch publication details: {str(e)}")
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