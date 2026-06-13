#!/usr/bin/env python3
"""
Khan Academy CCSS HS Algebra Scraper (Pilot)
Extracts exercise URLs for all HSA (High School Algebra) standards.

This is a focused scraper targeting HSA domain only to test the approach
before scaling to other HS domains (HSF, HSG, HSN, HSS).

Usage:
    python scrape_khan_hs_algebra.py          # Full HSA extraction
    python scrape_khan_hs_algebra.py --quick  # Test on first 5 standards
"""

import json
import time
import sys
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Configuration
BASE_URL = "https://www.khanacademy.org"
MATH_STANDARDS_URL = f"{BASE_URL}/standards/CCSS.Math"
OUTPUT_DIR = Path(__file__).parent / "data"
DELAY_BETWEEN_PAGES = 2.0  # seconds - be respectful

# All 48 HSA (High School Algebra) standards
# Format: (code, display_name) where code is the path segment
HSA_STANDARDS = [
    # A.APR - Arithmetic with Polynomials & Rational Expressions
    ("HSA/A_APR/A", "HSA.APR.A"),
    ("HSA/A_APR/A/1", "HSA.APR.A.1"),
    ("HSA/A_APR/B", "HSA.APR.B"),
    ("HSA/A_APR/B/2", "HSA.APR.B.2"),
    ("HSA/A_APR/B/3", "HSA.APR.B.3"),
    ("HSA/A_APR/C", "HSA.APR.C"),
    ("HSA/A_APR/C/4", "HSA.APR.C.4"),
    ("HSA/A_APR/C/5", "HSA.APR.C.5"),
    ("HSA/A_APR/D", "HSA.APR.D"),
    ("HSA/A_APR/D/6", "HSA.APR.D.6"),
    ("HSA/A_APR/D/7", "HSA.APR.D.7"),
    
    # A.CED - Creating Equations & Inequalities
    ("HSA/A_CED/A", "HSA.CED.A"),
    ("HSA/A_CED/A/1", "HSA.CED.A.1"),
    ("HSA/A_CED/A/2", "HSA.CED.A.2"),
    ("HSA/A_CED/A/3", "HSA.CED.A.3"),
    ("HSA/A_CED/A/4", "HSA.CED.A.4"),
    
    # A.REI - Reasoning with Equations & Inequalities
    ("HSA/A_REI/A", "HSA.REI.A"),
    ("HSA/A_REI/A/1", "HSA.REI.A.1"),
    ("HSA/A_REI/A/2", "HSA.REI.A.2"),
    ("HSA/A_REI/B", "HSA.REI.B"),
    ("HSA/A_REI/B/3", "HSA.REI.B.3"),
    ("HSA/A_REI/B/4", "HSA.REI.B.4"),
    ("HSA/A_REI/B/4_a", "HSA.REI.B.4.a"),
    ("HSA/A_REI/B/4_b", "HSA.REI.B.4.b"),
    ("HSA/A_REI/C", "HSA.REI.C"),
    ("HSA/A_REI/C/5", "HSA.REI.C.5"),
    ("HSA/A_REI/C/6", "HSA.REI.C.6"),
    ("HSA/A_REI/C/7", "HSA.REI.C.7"),
    ("HSA/A_REI/D", "HSA.REI.D"),
    ("HSA/A_REI/D/10", "HSA.REI.D.10"),
    ("HSA/A_REI/D/11", "HSA.REI.D.11"),
    ("HSA/A_REI/D/12", "HSA.REI.D.12"),
    
    # A.SSE - Seeing Structure in Expressions
    ("HSA/A_SSE/A", "HSA.SSE.A"),
    ("HSA/A_SSE/A/1", "HSA.SSE.A.1"),
    ("HSA/A_SSE/A/1_a", "HSA.SSE.A.1.a"),
    ("HSA/A_SSE/A/1_b", "HSA.SSE.A.1.b"),
    ("HSA/A_SSE/A/2", "HSA.SSE.A.2"),
    ("HSA/A_SSE/B", "HSA.SSE.B"),
    ("HSA/A_SSE/B/3", "HSA.SSE.B.3"),
    ("HSA/A_SSE/B/3_b", "HSA.SSE.B.3.b"),
    ("HSA/A_SSE/B/3_c", "HSA.SSE.B.3.c"),
    ("HSA/A_SSE/B/4", "HSA.SSE.B.4"),
]

def log(msg):
    """Timestamped logging."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def save_checkpoint(data, filename):
    """Save data to JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log(f"✓ Saved: {filepath}")

def scrape_standard_page(page, standard_code_path, standard_display):
    """
    Scrape a single standard page (e.g., /standards/CCSS.Math/HSA/A_SSE/A/1)
    Extract exercise URLs and metadata.
    """
    full_url = f"{BASE_URL}/standards/CCSS.Math/{standard_code_path}"
    log(f"  Scraping {standard_display}: {full_url}")
    
    try:
        page.goto(full_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(5)  # Wait for React rendering
    except PlaywrightTimeout:
        log(f"    ⚠ TIMEOUT loading {full_url}")
        return None
    except Exception as e:
        log(f"    ✗ ERROR: {e}")
        return None

    standard_data = {
        'code': standard_display,
        'url': full_url,
        'scraped_at': datetime.now().isoformat(),
        'exercises': [],
        'videos': [],
        'articles': []
    }

    # Extract exercise links (strategy 1: direct href matching)
    try:
        all_links = page.query_selector_all('a[href]')
        seen_urls = set()
        
        for link in all_links:
            try:
                href = link.get_attribute('href') or ''
                text = link.inner_text().strip()
                
                if not text or len(text) < 2 or href in seen_urls:
                    continue
                
                seen_urls.add(href)
                full_url_link = href if href.startswith('http') else f"{BASE_URL}{href}"
                
                # Categorize links
                if '/exercise/' in href or '/e/' in href:
                    standard_data['exercises'].append({
                        'title': text,
                        'url': full_url_link,
                        'type': 'exercise'
                    })
                elif '/v/' in href or '/video/' in href:
                    standard_data['videos'].append({
                        'title': text,
                        'url': full_url_link,
                        'type': 'video'
                    })
                elif '/a/' in href or '/article/' in href:
                    standard_data['articles'].append({
                        'title': text,
                        'url': full_url_link,
                        'type': 'article'
                    })
            except Exception:
                continue
    except Exception as e:
        log(f"    ⚠ Error extracting links: {e}")

    ex_count = len(standard_data['exercises'])
    vid_count = len(standard_data['videos'])
    log(f"    ✓ Found {ex_count} exercises, {vid_count} videos")
    
    return standard_data

def main():
    quick_mode = '--quick' in sys.argv
    standards_to_scrape = HSA_STANDARDS[:5] if quick_mode else HSA_STANDARDS
    
    log("=" * 70)
    log("Khan Academy HSA (High School Algebra) Scraper - PILOT")
    log(f"Mode: {'QUICK TEST (5 standards)' if quick_mode else 'FULL EXTRACTION (48 standards)'}")
    log("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            slow_mo=100  # 100ms delay between actions for stability
        )
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        page.set_default_timeout(30000)

        all_results = []
        total = len(standards_to_scrape)
        
        for i, (code_path, display) in enumerate(standards_to_scrape):
            log(f"\n[{i+1}/{total}] Scraping standard...")
            
            result = scrape_standard_page(page, code_path, display)
            if result:
                all_results.append(result)
                
                # Save checkpoint every 10 standards
                if (i + 1) % 10 == 0 or quick_mode or i == total - 1:
                    save_checkpoint(all_results, 'khan_hs_algebra_results.json')
            
            # Respectful delay between pages
            if i < total - 1:
                time.sleep(DELAY_BETWEEN_PAGES)

        # Final summary
        log("\n" + "=" * 70)
        log("EXTRACTION COMPLETE")
        log(f"Standards scraped: {len(all_results)}/{total}")
        total_exercises = sum(len(r.get('exercises', [])) for r in all_results)
        total_videos = sum(len(r.get('videos', [])) for r in all_results)
        log(f"Total exercises: {total_exercises}")
        log(f"Total videos: {total_videos}")
        log("=" * 70)

        browser.close()

if __name__ == '__main__':
    main()
