#!/usr/bin/env python3
"""
Khan Academy CCSS Math Standards Scraper
Extracts standard descriptions and linked practice problems/exercises
using Playwright browser automation.

Usage:
    python scrape_khan_ccss.py          # Full extraction
    python scrape_khan_ccss.py --test   # Test on K.CC only
"""

import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Configuration
BASE_URL = "https://www.khanacademy.org"
MATH_STANDARDS_URL = f"{BASE_URL}/standards/CCSS.Math"
OUTPUT_DIR = Path(__file__).parent / "data"
DELAY_BETWEEN_PAGES = 2.0  # seconds - be respectful
DELAY_BETWEEN_CLICKS = 1.0

def log(msg):
    """Simple timestamped logging."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def save_checkpoint(data, filename):
    """Save data to JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log(f"  Saved checkpoint: {filepath}")


def scrape_standard_page(page, standard_url, standard_code):
    """
    Navigate to a specific standard page (e.g., /standards/CCSS.Math/K.CC)
    and extract:
    - Standard description/title
    - Sub-standards with descriptions
    - Linked exercises/practice problems
    """
    full_url = f"{BASE_URL}{standard_url}" if standard_url.startswith('/') else standard_url
    log(f"  Navigating to: {full_url}")
    
    try:
        page.goto(full_url, wait_until="domcontentloaded", timeout=20000)
        # Give React time to render
        time.sleep(4)
    except PlaywrightTimeout:
        log(f"  TIMEOUT loading {full_url}")
        return None
    except Exception as e:
        log(f"  ERROR loading {full_url}: {e}")
        return None

    # Wait for content to appear
    try:
        page.wait_for_selector('[data-test-id]', timeout=10000)
    except PlaywrightTimeout:
        # Try alternative: wait for any meaningful content
        try:
            page.wait_for_selector('h2, h3, [class*="standard"]', timeout=5000)
        except PlaywrightTimeout:
            log(f"  WARNING: No content selectors found on {full_url}")

    # Extract page content using multiple strategies
    standard_data = {
        'code': standard_code,
        'url': full_url,
        'scraped_at': datetime.now().isoformat(),
        'title': None,
        'description': None,
        'sub_standards': [],
        'exercises': [],
        'videos': [],
        'articles': []
    }

    # Strategy 1: Extract all text content from main area
    # Get the page title/heading
    try:
        # Try to get the main heading
        headings = page.query_selector_all('h1, h2')
        for h in headings:
            text = h.inner_text().strip()
            if text and standard_code.replace('CCSS.Math/', '') in text:
                standard_data['title'] = text
                break
            elif text and len(text) > 5:
                if not standard_data['title']:
                    standard_data['title'] = text
    except Exception as e:
        log(f"  Warning: Could not extract headings: {e}")

    # Strategy 2: Extract all links that look like exercises or content
    try:
        all_links = page.query_selector_all('a[href]')
        for link in all_links:
            try:
                href = link.get_attribute('href') or ''
                text = link.inner_text().strip()
                
                if not text or len(text) < 3:
                    continue
                    
                # Categorize links
                if '/exercise/' in href or '/e/' in href:
                    standard_data['exercises'].append({
                        'title': text,
                        'url': href if href.startswith('http') else f"{BASE_URL}{href}",
                        'type': 'exercise'
                    })
                elif '/v/' in href or '/video/' in href:
                    standard_data['videos'].append({
                        'title': text,
                        'url': href if href.startswith('http') else f"{BASE_URL}{href}",
                        'type': 'video'
                    })
                elif '/a/' in href or '/article/' in href:
                    standard_data['articles'].append({
                        'title': text,
                        'url': href if href.startswith('http') else f"{BASE_URL}{href}",
                        'type': 'article'
                    })
            except Exception:
                continue
    except Exception as e:
        log(f"  Warning: Could not extract links: {e}")

    # Strategy 3: Extract structured content blocks
    # Look for sub-standard descriptions (usually in expandable sections)
    try:
        # Look for elements that contain standard codes like K.CC.A.1
        all_elements = page.query_selector_all('[class*="Standard"], [class*="standard"], li, [role="listitem"]')
        for el in all_elements:
            try:
                text = el.inner_text().strip()
                # Check if it looks like a sub-standard (e.g., "K.CC.A.1 Know number names...")
                if text and ('.' in text[:10]) and len(text) > 10:
                    # Try to split code from description
                    parts = text.split('\n')
                    if len(parts) >= 1:
                        standard_data['sub_standards'].append({
                            'text': text[:500]  # Limit length
                        })
            except Exception:
                continue
    except Exception as e:
        log(f"  Warning: Could not extract sub-standards: {e}")

    # Strategy 4: Get full page text as fallback for rich descriptions
    try:
        body_text = page.inner_text('body')
        # Extract meaningful paragraphs (likely descriptions)
        paragraphs = [p.strip() for p in body_text.split('\n') if len(p.strip()) > 50]
        # Filter out navigation/boilerplate
        meaningful = [p for p in paragraphs if not any(skip in p.lower() for skip in 
                     ['sign up', 'log in', 'donate', 'khan academy', 'our mission', 
                      'copyright', 'terms of', 'privacy'])]
        if meaningful:
            standard_data['description'] = '\n'.join(meaningful[:10])  # First 10 meaningful paragraphs
    except Exception as e:
        log(f"  Warning: Could not extract page text: {e}")

    # Remove duplicates from exercises
    seen_urls = set()
    unique_exercises = []
    for ex in standard_data['exercises']:
        if ex['url'] not in seen_urls:
            seen_urls.add(ex['url'])
            unique_exercises.append(ex)
    standard_data['exercises'] = unique_exercises

    return standard_data


def scrape_standards_index(page):
    """
    Navigate to the main CCSS.Math standards page and extract
    all standard domain links from the collapsible grade sections.
    """
    log(f"Loading standards index: {MATH_STANDARDS_URL}")
    page.goto(MATH_STANDARDS_URL, wait_until="domcontentloaded", timeout=20000)
    time.sleep(5)  # Extra time for React

    # Try to find and click grade-level expandable sections
    standard_links = []
    
    # First, try to expand all collapsible sections
    try:
        # Look for clickable grade section headers
        expandable = page.query_selector_all('button, [role="button"], [aria-expanded]')
        log(f"  Found {len(expandable)} expandable elements")
        
        for btn in expandable:
            try:
                text = btn.inner_text().strip()
                if any(g in text for g in ['Grade', 'Kindergarten', 'High School']):
                    btn.click()
                    time.sleep(DELAY_BETWEEN_CLICKS)
                    log(f"  Expanded: {text[:50]}")
            except Exception:
                continue
    except Exception as e:
        log(f"  Warning expanding sections: {e}")

    time.sleep(2)  # Wait for expansions to settle

    # Now extract all standard links
    try:
        all_links = page.query_selector_all('a[href*="/standards/CCSS.Math/"]')
        log(f"  Found {len(all_links)} standard links")
        
        for link in all_links:
            try:
                href = link.get_attribute('href')
                text = link.inner_text().strip()
                if href and text and href != '/standards/CCSS.Math':
                    # Extract the standard code from the URL
                    code = href.split('/standards/CCSS.Math/')[-1] if '/standards/CCSS.Math/' in href else ''
                    if code and code not in [sl['code'] for sl in standard_links]:
                        standard_links.append({
                            'code': code,
                            'title': text,
                            'url': href
                        })
            except Exception:
                continue
    except Exception as e:
        log(f"  Error extracting links: {e}")

    # If we didn't find links via href, try extracting from page text
    if not standard_links:
        log("  No links found via selector, trying full page analysis...")
        try:
            body_text = page.inner_text('body')
            log(f"  Page text length: {len(body_text)} chars")
            # Log first 500 chars for debugging
            log(f"  Page start: {body_text[:500]}")
        except Exception as e:
            log(f"  Could not get page text: {e}")

    return standard_links


def main():
    test_mode = '--test' in sys.argv
    
    log("=" * 60)
    log("Khan Academy CCSS Math Standards Scraper")
    log(f"Mode: {'TEST (K.CC only)' if test_mode else 'FULL EXTRACTION'}")
    log("=" * 60)

    with sync_playwright() as p:
        # Launch browser (headless for speed, set False for debugging)
        browser = p.chromium.launch(
            headless=True,
            slow_mo=100
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        page.set_default_timeout(30000)

        if test_mode:
            # Skip index discovery, go straight to K.CC
            log("\n--- TEST MODE: Scraping K.CC directly ---")
            standard_links = []
            targets = [{'code': 'K.CC', 'url': '/standards/CCSS.Math/K.CC', 'title': 'Counting & Cardinality'}]
        else:
            # Step 1: Get list of all standard domain pages
            log("\n--- PHASE 1: Discovering standard links ---")
            standard_links = scrape_standards_index(page)
            log(f"\nFound {len(standard_links)} standard domains to scrape")
            
            if standard_links:
                save_checkpoint(standard_links, 'standard_links_index.json')
                for sl in standard_links[:5]:
                    log(f"  {sl['code']}: {sl['title'][:60]}")
                if len(standard_links) > 5:
                    log(f"  ... and {len(standard_links) - 5} more")
            targets = standard_links

        # Step 2: Scrape each standard page
        log("\n--- PHASE 2: Scraping individual standard pages ---")
            
        all_results = []
        for i, target in enumerate(targets):
            log(f"\n[{i+1}/{len(targets)}] Scraping: {target['code']} - {target.get('title', 'N/A')}")
            
            result = scrape_standard_page(page, target['url'], target['code'])
            if result:
                all_results.append(result)
                exercise_count = len(result.get('exercises', []))
                video_count = len(result.get('videos', []))
                log(f"  Results: {exercise_count} exercises, {video_count} videos")
                
                # Save after each standard (checkpoint)
                if (i + 1) % 5 == 0 or test_mode:
                    save_checkpoint(all_results, 'khan_ccss_math_results.json')
            
            # Be respectful with delays
            if i < len(targets) - 1:
                time.sleep(DELAY_BETWEEN_PAGES)

        # Final save
        save_checkpoint(all_results, 'khan_ccss_math_results.json')
        
        # Summary
        log("\n" + "=" * 60)
        log("EXTRACTION COMPLETE")
        log(f"Standards scraped: {len(all_results)}")
        total_exercises = sum(len(r.get('exercises', [])) for r in all_results)
        total_videos = sum(len(r.get('videos', [])) for r in all_results)
        log(f"Total exercises found: {total_exercises}")
        log(f"Total videos found: {total_videos}")
        log("=" * 60)

        browser.close()


if __name__ == '__main__':
    main()
