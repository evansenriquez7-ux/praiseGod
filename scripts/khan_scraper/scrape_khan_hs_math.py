#!/usr/bin/env python3
"""
Khan Academy CCSS High School Math Scraper

Scrapes exercises from Khan Academy's CCSS.Math/HS* standards pages.
Uses Playwright for React SPA rendering.

Strategy:
- Navigate to each sub-domain page (e.g., /standards/CCSS.Math/HSA.SSE)
- Page has hierarchical headings: H2=cluster, H3=standard, H4=sub-standard
- Exercise/video links are listed under their parent standard
- Extract all exercises grouped by their standard code
- Map KA codes (HSA.SSE.A.1) -> CCMed codes (A_SSE_A_1)

Usage:
    python scrape_khan_hs_math.py                # Full HS extraction (all 5 domains)
    python scrape_khan_hs_math.py --pilot        # Pilot: HSA (Algebra) only
    python scrape_khan_hs_math.py --domain HSF   # Single domain
    python scrape_khan_hs_math.py --test         # Quick test on HSA.SSE only
"""

import json
import time
import sys
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Configuration
BASE_URL = "https://www.khanacademy.org"
OUTPUT_DIR = Path(__file__).parent / "data"
DELAY_BETWEEN_PAGES = 3.0  # seconds - be respectful

# HS Math sub-domain pages (the actual content pages with exercises)
# Format: { sub_domain_url: { "name": ..., "parent_domain": ... } }
HS_SUB_DOMAINS = {
    # High School Algebra
    "HSA.SSE": {"name": "Seeing Structure in Expressions", "parent": "HSA"},
    "HSA.APR": {"name": "Arithmetic with Polynomials & Rational Expressions", "parent": "HSA"},
    "HSA.CED": {"name": "Creating Equations", "parent": "HSA"},
    "HSA.REI": {"name": "Reasoning with Equations & Inequalities", "parent": "HSA"},
    # High School Functions
    "HSF.IF":  {"name": "Interpreting Functions", "parent": "HSF"},
    "HSF.BF":  {"name": "Building Functions", "parent": "HSF"},
    "HSF.LE":  {"name": "Linear, Quadratic & Exponential Models", "parent": "HSF"},
    "HSF.TF":  {"name": "Trigonometric Functions", "parent": "HSF"},
    # High School Geometry
    "HSG.CO":  {"name": "Congruence", "parent": "HSG"},
    "HSG.SRT": {"name": "Similarity, Right Triangles & Trigonometry", "parent": "HSG"},
    "HSG.C":   {"name": "Circles", "parent": "HSG"},
    "HSG.GPE": {"name": "Geometric Properties with Equations", "parent": "HSG"},
    "HSG.GMD": {"name": "Geometric Measurement & Dimension", "parent": "HSG"},
    "HSG.MG":  {"name": "Modeling with Geometry", "parent": "HSG"},
    # High School Number & Quantity
    "HSN.RN":  {"name": "The Real Number System", "parent": "HSN"},
    "HSN.Q":   {"name": "Quantities", "parent": "HSN"},
    "HSN.CN":  {"name": "The Complex Number System", "parent": "HSN"},
    # High School Statistics & Probability
    "HSS.ID":  {"name": "Interpreting Categorical & Quantitative Data", "parent": "HSS"},
    "HSS.IC":  {"name": "Making Inferences & Justifying Conclusions", "parent": "HSS"},
    "HSS.CP":  {"name": "Conditional Probability & Rules of Probability", "parent": "HSS"},
    "HSS.MD":  {"name": "Using Probability to Make Decisions", "parent": "HSS"},
}

# Groupings for pilot/domain modes
DOMAINS = {
    "HSA": ["HSA.SSE", "HSA.APR", "HSA.CED", "HSA.REI"],
    "HSF": ["HSF.IF", "HSF.BF", "HSF.LE", "HSF.TF"],
    "HSG": ["HSG.CO", "HSG.SRT", "HSG.C", "HSG.GPE", "HSG.GMD", "HSG.MG"],
    "HSN": ["HSN.RN", "HSN.Q", "HSN.CN"],
    "HSS": ["HSS.ID", "HSS.IC", "HSS.CP", "HSS.MD"],
}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def save_json(data, filename):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    log(f"  Saved: {filepath}")
    return filepath


def ka_code_to_ccmed(ka_code):
    """
    Convert Khan Academy standard code to CCMed file naming convention.
    HSA.SSE.A.1.a -> A_SSE_A_1a
    HSA.SSE.A.1   -> A_SSE_A_1
    HSA.SSE.A     -> A_SSE_A
    HSF.IF.C.7.a  -> F_IF_C_7a  (note: no underscore before lowercase letter)
    """
    # Remove the HS prefix (HSA -> A, HSF -> F, HSG -> G, HSN -> N, HSS -> S)
    code = ka_code
    for prefix in ["HSA.", "HSF.", "HSG.", "HSN.", "HSS."]:
        if code.startswith(prefix):
            code = code[2:]  # Remove "HS" part, keep "A.", "F.", etc.
            break
    
    # Replace dots with underscores
    parts = code.split('.')
    
    # Handle trailing lowercase letters (sub-parts like .a, .b, .c)
    # These attach to the previous number without underscore in CCMed
    # e.g., A.SSE.A.1.a -> A_SSE_A_1a
    if len(parts) >= 1 and len(parts[-1]) == 1 and parts[-1].islower():
        last_letter = parts.pop()
        if parts:
            parts[-1] = parts[-1] + last_letter
    
    return '_'.join(parts)


def scrape_sub_domain_page(page, sub_domain_code):
    """
    Scrape a sub-domain page (e.g., /standards/CCSS.Math/HSA.SSE).
    
    The page has this structure:
    - H2: cluster code (HSA.SSE.A - "Interpret the structure of expressions")
    - H3: standard code (HSA.SSE.A.1 - "Interpret expressions...")
    - H4: sub-standard code (HSA.SSE.A.1.a - "Interpret parts of an expression...")
    - Under each: exercise/video links listed as text items
    
    Returns a dict mapping standard codes to their exercises.
    """
    url = f"{BASE_URL}/standards/CCSS.Math/{sub_domain_code}"
    info = HS_SUB_DOMAINS[sub_domain_code]
    
    log(f"\n{'='*60}")
    log(f"Scraping: {sub_domain_code} - {info['name']}")
    log(f"URL: {url}")
    
    try:
        page.goto(url, wait_until="networkidle", timeout=45000)
    except PlaywrightTimeout:
        log(f"  TIMEOUT (networkidle), retrying with domcontentloaded...")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(10)
        except Exception as e:
            log(f"  FAILED to load page: {e}")
            return None
    except Exception as e:
        log(f"  ERROR loading page: {e}")
        return None
    
    # Wait for content to render
    time.sleep(5)
    
    # Use JavaScript to extract the full hierarchical structure
    # This avoids EPIPE issues from many individual DOM queries
    data = page.evaluate('''(subDomainCode) => {
        const BASE = "https://www.khanacademy.org";
        const results = {
            standards: {},
            all_exercises: [],
            all_videos: [],
            page_title: document.title,
            raw_headings: []
        };
        
        // Find all heading elements that contain standard codes
        const headings = document.querySelectorAll('h2, h3, h4, h5');
        let currentStandard = null;
        
        for (const h of headings) {
            const text = h.innerText.trim();
            // Check if this is a standard code heading
            const codeMatch = text.match(/^(HS[AFGSN]\\.[A-Z]+\\.[A-Z](?:\\.\\d+[a-z]?)?)/);
            if (codeMatch) {
                currentStandard = codeMatch[1];
                results.raw_headings.push({
                    code: currentStandard,
                    tag: h.tagName,
                    text: text.substring(0, 300)
                });
                
                if (!results.standards[currentStandard]) {
                    results.standards[currentStandard] = {
                        code: currentStandard,
                        description: text.replace(currentStandard, '').trim(),
                        exercises: [],
                        videos: [],
                        articles: []
                    };
                }
            }
        }
        
        // Now find all exercise/video links and associate them with the nearest preceding standard
        // Walk through all elements in document order
        const allElements = document.querySelectorAll('h2, h3, h4, h5, a[href]');
        currentStandard = null;
        
        for (const el of allElements) {
            if (['H2', 'H3', 'H4', 'H5'].includes(el.tagName)) {
                const text = el.innerText.trim();
                const codeMatch = text.match(/^(HS[AFGSN]\\.[A-Z]+\\.[A-Z](?:\\.\\d+[a-z]?)?)/);
                if (codeMatch) {
                    currentStandard = codeMatch[1];
                }
            } else if (el.tagName === 'A' && currentStandard) {
                const href = el.getAttribute('href') || '';
                const title = el.innerText.trim();
                
                if (!title || title.length < 3) continue;
                
                const fullUrl = href.startsWith('http') ? href : BASE + href;
                
                if (href.includes('/e/') || href.includes('/exercise/')) {
                    const entry = {title, url: fullUrl, type: 'exercise'};
                    if (results.standards[currentStandard]) {
                        results.standards[currentStandard].exercises.push(entry);
                    }
                    results.all_exercises.push({...entry, standard: currentStandard});
                } else if (href.includes('/v/') || href.includes('/video/')) {
                    const entry = {title, url: fullUrl, type: 'video'};
                    if (results.standards[currentStandard]) {
                        results.standards[currentStandard].videos.push(entry);
                    }
                    results.all_videos.push({...entry, standard: currentStandard});
                } else if (href.includes('/a/') || href.includes('/article/')) {
                    const entry = {title, url: fullUrl, type: 'article'};
                    if (results.standards[currentStandard]) {
                        results.standards[currentStandard].articles.push(entry);
                    }
                }
            }
        }
        
        return results;
    }''', sub_domain_code)
    
    # Process results
    standards = data.get("standards", {})
    all_exercises = data.get("all_exercises", [])
    all_videos = data.get("all_videos", [])
    
    log(f"  Found {len(standards)} standard codes")
    log(f"  Total exercises: {len(all_exercises)}")
    log(f"  Total videos: {len(all_videos)}")
    
    # Log breakdown per standard
    for code, std_data in sorted(standards.items()):
        ex_count = len(std_data.get("exercises", []))
        if ex_count > 0:
            log(f"    {code}: {ex_count} exercises")
    
    # Add CCMed mapping
    for code, std_data in standards.items():
        std_data["ccmed_code"] = ka_code_to_ccmed(code)
    
    result = {
        "sub_domain": sub_domain_code,
        "name": info["name"],
        "parent": info["parent"],
        "url": url,
        "scraped_at": datetime.now().isoformat(),
        "standards": standards,
        "total_exercises": len(all_exercises),
        "total_videos": len(all_videos),
        "raw_headings": data.get("raw_headings", [])
    }
    
    return result


def main():
    # Parse arguments
    pilot_mode = '--pilot' in sys.argv
    test_mode = '--test' in sys.argv
    domain_arg = None
    for i, arg in enumerate(sys.argv):
        if arg == '--domain' and i + 1 < len(sys.argv):
            domain_arg = sys.argv[i + 1].upper()
    
    # Determine which sub-domains to scrape
    if test_mode:
        sub_domains_to_scrape = ["HSA.SSE"]
        mode_label = "TEST (HSA.SSE only)"
    elif pilot_mode:
        sub_domains_to_scrape = DOMAINS["HSA"]
        mode_label = "PILOT (HSA - all 4 sub-domains)"
    elif domain_arg:
        if domain_arg in DOMAINS:
            sub_domains_to_scrape = DOMAINS[domain_arg]
            mode_label = f"SINGLE DOMAIN ({domain_arg})"
        else:
            print(f"Error: Unknown domain '{domain_arg}'. Valid: {list(DOMAINS.keys())}")
            sys.exit(1)
    else:
        sub_domains_to_scrape = list(HS_SUB_DOMAINS.keys())
        mode_label = "FULL (all 21 sub-domains)"
    
    log("=" * 60)
    log("Khan Academy HS Math CCSS Standards Scraper")
    log(f"Mode: {mode_label}")
    log(f"Sub-domains: {sub_domains_to_scrape}")
    log(f"Output: {OUTPUT_DIR}")
    log("=" * 60)
    
    all_results = {}
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1440, 'height': 900}
        )
        page = context.new_page()
        page.set_default_timeout(45000)
        
        for i, sub_domain in enumerate(sub_domains_to_scrape):
            log(f"\n[{i+1}/{len(sub_domains_to_scrape)}] Processing {sub_domain}")
            
            result = scrape_sub_domain_page(page, sub_domain)
            
            if result:
                all_results[sub_domain] = result
                # Save per-sub-domain checkpoint
                save_json(result, f"khan_hs_{sub_domain.lower().replace('.', '_')}.json")
            else:
                log(f"  FAILED: {sub_domain}")
            
            # Respectful delay between pages
            if i < len(sub_domains_to_scrape) - 1:
                time.sleep(DELAY_BETWEEN_PAGES)
        
        browser.close()
    
    # Save combined results
    save_json(all_results, "khan_ccss_hs_math_all.json")
    
    # Generate CCMed mapping summary
    ccmed_mapping = {}  # ccmed_code -> [exercises]
    for sub_domain, result in all_results.items():
        for ka_code, std_data in result.get("standards", {}).items():
            ccmed_code = std_data.get("ccmed_code", ka_code_to_ccmed(ka_code))
            if ccmed_code not in ccmed_mapping:
                ccmed_mapping[ccmed_code] = {
                    "ka_code": ka_code,
                    "ccmed_code": ccmed_code,
                    "sub_domain": sub_domain,
                    "exercises": [],
                    "videos": []
                }
            ccmed_mapping[ccmed_code]["exercises"].extend(std_data.get("exercises", []))
            ccmed_mapping[ccmed_code]["videos"].extend(std_data.get("videos", []))
    
    save_json(ccmed_mapping, "khan_hs_ccmed_mapping.json")
    
    # Summary
    log("\n" + "=" * 60)
    log("EXTRACTION COMPLETE")
    log("=" * 60)
    
    total_exercises = 0
    total_standards = 0
    standards_with_exercises = 0
    
    for sub_domain, result in all_results.items():
        standards = result.get("standards", {})
        ex_count = result.get("total_exercises", 0)
        total_exercises += ex_count
        total_standards += len(standards)
        standards_with_exercises += sum(1 for s in standards.values() if len(s.get("exercises", [])) > 0)
        log(f"  {sub_domain}: {len(standards)} standards, {ex_count} exercises")
    
    log(f"\n  TOTALS:")
    log(f"    Sub-domains scraped: {len(all_results)}")
    log(f"    Standard codes found: {total_standards}")
    log(f"    Standards with exercises: {standards_with_exercises}")
    log(f"    Total exercises: {total_exercises}")
    log(f"    CCMed codes mapped: {len(ccmed_mapping)}")
    log(f"\n  Files saved to: {OUTPUT_DIR}")
    log("=" * 60)


if __name__ == '__main__':
    main()
