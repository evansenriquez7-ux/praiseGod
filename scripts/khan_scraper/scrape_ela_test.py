#!/usr/bin/env python3
"""
Quick test: Scrape Khan Academy CCSS ELA Language Standards for grades K-2.
URL pattern: https://www.khanacademy.org/standards/CCSSELA/{code}

Language standards codes for K-2:
- L.K (Kindergarten Language)
- L.1 (Grade 1 Language)
- L.2 (Grade 2 Language)
"""

import json
import time
import sys
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

BASE_URL = "https://www.khanacademy.org"
OUTPUT_DIR = Path(__file__).parent / "data"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def scrape_ela_standard(page, standard_code):
    """Scrape a single ELA standard page."""
    url = f"{BASE_URL}/standards/CCSSELA/{standard_code}"
    log(f"  Navigating to: {url}")
    
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        time.sleep(4)
    except PlaywrightTimeout:
        log(f"  TIMEOUT: {url}")
        return None
    except Exception as e:
        log(f"  ERROR: {e}")
        return None

    # Wait for React render
    try:
        page.wait_for_selector('a[href]', timeout=10000)
    except PlaywrightTimeout:
        log(f"  WARNING: No links rendered")

    result = {
        'code': standard_code,
        'url': url,
        'scraped_at': datetime.now().isoformat(),
        'title': None,
        'description': None,
        'exercises': [],
        'videos': [],
        'articles': [],
        'sub_standards': []
    }

    # Get headings
    try:
        headings = page.query_selector_all('h1, h2, h3')
        for h in headings:
            text = h.inner_text().strip()
            if text and len(text) > 3 and not result['title']:
                result['title'] = text
    except Exception:
        pass

    # Get all links - exercises, videos, articles
    try:
        all_links = page.query_selector_all('a[href]')
        for link in all_links:
            try:
                href = link.get_attribute('href') or ''
                text = link.inner_text().strip()
                if not text or len(text) < 3:
                    continue
                
                full_url = href if href.startswith('http') else f"{BASE_URL}{href}"
                
                if '/exercise/' in href or '/e/' in href:
                    result['exercises'].append({'title': text, 'url': full_url, 'type': 'exercise'})
                elif '/v/' in href or '/video/' in href:
                    result['videos'].append({'title': text, 'url': full_url, 'type': 'video'})
                elif '/a/' in href or '/article/' in href:
                    result['articles'].append({'title': text, 'url': full_url, 'type': 'article'})
            except Exception:
                continue
    except Exception as e:
        log(f"  Error extracting links: {e}")

    # Get rich description from page body
    try:
        body_text = page.inner_text('body')
        paragraphs = [p.strip() for p in body_text.split('\n') if len(p.strip()) > 40]
        meaningful = [p for p in paragraphs if not any(skip in p.lower() for skip in 
                     ['sign up', 'log in', 'donate', 'khan academy', 'our mission', 
                      'copyright', 'terms of', 'privacy', 'cookie', 'courses'])]
        if meaningful:
            result['description'] = '\n'.join(meaningful[:15])
    except Exception:
        pass

    # Deduplicate exercises
    seen = set()
    unique = []
    for ex in result['exercises']:
        if ex['url'] not in seen:
            seen.add(ex['url'])
            unique.append(ex)
    result['exercises'] = unique

    return result


def main():
    # ELA Language Standards for K-2
    targets = [
        {'code': 'L.K', 'title': 'Language - Kindergarten'},
        {'code': 'L.1', 'title': 'Language - Grade 1'},
        {'code': 'L.2', 'title': 'Language - Grade 2'},
    ]

    log("=" * 60)
    log("Khan Academy CCSS ELA Language Standards Scraper (K-2 Test)")
    log("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, slow_mo=100)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        page.set_default_timeout(20000)

        all_results = []
        for i, target in enumerate(targets):
            log(f"\n[{i+1}/{len(targets)}] Scraping: {target['code']} - {target['title']}")
            result = scrape_ela_standard(page, target['code'])
            
            if result:
                all_results.append(result)
                log(f"  Exercises: {len(result['exercises'])}")
                log(f"  Videos: {len(result['videos'])}")
                log(f"  Articles: {len(result['articles'])}")
                if result['description']:
                    log(f"  Description: {result['description'][:100]}...")
            else:
                log(f"  FAILED to scrape {target['code']}")

            if i < len(targets) - 1:
                time.sleep(2)

        # Save results
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / 'khan_ccss_ela_language_k2.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        log(f"\nSaved to: {output_path}")

        # Summary
        log("\n" + "=" * 60)
        log("RESULTS SUMMARY")
        total_ex = sum(len(r.get('exercises', [])) for r in all_results)
        total_vid = sum(len(r.get('videos', [])) for r in all_results)
        total_art = sum(len(r.get('articles', [])) for r in all_results)
        log(f"Standards scraped: {len(all_results)}")
        log(f"Total exercises: {total_ex}")
        log(f"Total videos: {total_vid}")
        log(f"Total articles: {total_art}")
        log("=" * 60)

        browser.close()


if __name__ == '__main__':
    main()
