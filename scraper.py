import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# Target configuration
TARGET_URL = "billiontoone.com/about/leadership-board"
SEARCH_TERM = "Dhruv"
# Format: YYYYMMDD (18 months ago from Nov 2026 is approx May 2025)
START_DATE = "20250501" 

def fetch_wayback_snapshots():
    print(f"Querying Wayback Machine CDX API for {TARGET_URL}...")
    
    # CDX API: collapse=timestamp:6 ensures we only get 1 snapshot per month (YYYYMM)
    cdx_url = (
        f"http://web.archive.org/cdx/search/cdx?"
        f"url={TARGET_URL}&output=json&fl=timestamp,original&"
        f"from={START_DATE}&collapse=timestamp:6"
    )
    
    response = requests.get(cdx_url)
    if response.status_code != 200:
        print("Failed to fetch CDX data.")
        return []

    data = response.json()
    if len(data) < 2:
        print("No snapshots found in the specified timeframe.")
        return []

    # Skip header row [0]
    return data[1:]

def analyze_snapshots(snapshots):
    for timestamp, original_url in snapshots:
        snapshot_url = f"http://web.archive.org/web/{timestamp}/{original_url}"
        dt = datetime.strptime(timestamp, "%Y%m%d%H%M%S")
        print(f"\n--- Analyzing Snapshot: {dt.strftime('%B %Y')} ---")
        print(f"URL: {snapshot_url}")
        
        try:
            # Add a user-agent to prevent blocking
            headers = {'User-Agent': 'Mozilla/5.0'}
            html_resp = requests.get(snapshot_url, headers=headers, timeout=15)
            
            if html_resp.status_code != 200:
                print("Failed to load snapshot HTML.")
                time.sleep(2)
                continue
                
            soup = BeautifulSoup(html_resp.text, 'html.parser')
            
            # Search for the name
            found_elements = soup.find_all(string=lambda text: text and SEARCH_TERM in text)
            
            if not found_elements:
                print(f"Result: '{SEARCH_TERM}' NOT FOUND on page.")
            else:
                print(f"Result: '{SEARCH_TERM}' FOUND.")
                for el in found_elements:
                    parent = el.parent
                    # Walk up the DOM to find section headers or defining structural div classes
                    section_container = parent.find_parent(['section', 'div'], class_=True)
                    if section_container:
                        container_classes = " ".join(section_container.get('class', []))
                        # Look for preceding h2/h3 tags that define the section (e.g., "Executive Leadership Team")
                        heading = section_container.find_previous(['h2', 'h3'])
                        heading_text = heading.text.strip() if heading else "No prior heading found"
                        
                        print(f"  -> Contained in section heading: {heading_text}")
                        print(f"  -> DOM Container Classes: {container_classes}")
                    
        except Exception as e:
            print(f"Error parsing snapshot: {e}")
            
        # Be polite to the archive servers
        time.sleep(2)

if __name__ == "__main__":
    snapshots = fetch_wayback_snapshots()
    if snapshots:
        print(f"Found {len(snapshots)} monthly snapshots. Beginning extraction...")
        analyze_snapshots(snapshots)
