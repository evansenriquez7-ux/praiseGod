"""
Scrape Khan Academy CCSS ELA standards for grades 9-10.
Only RL.9-10, RI.9-10, and L.9-10 have content (W.9-10 and SL.9-10 are empty).
"""

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

OUTPUT = Path(__file__).parent / "data" / "khan_ccss_ela_9_10.json"
STANDARDS = ["RL.9-10", "RI.9-10", "L.9-10"]
BASE_URL = "https://www.khanacademy.org"


def scrape_standard(page, code):
    url = f"{BASE_URL}/standards/CCSSELA/{code}"
    print(f"\nScraping {code}: {url}", flush=True)

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
    except PlaywrightTimeout:
        print(f"  TIMEOUT loading {url}")
        return None
    except Exception as e:
        print(f"  ERROR loading: {e}")
        return None

    time.sleep(8)  # KA is heavy React SPA — wait longer

    # Expand all collapsed sections
    for _ in range(4):
        try:
            buttons = page.query_selector_all("button[aria-expanded='false']")
            if not buttons:
                break
            for btn in buttons:
                try:
                    btn.click()
                    time.sleep(0.2)
                except Exception:
                    pass
            time.sleep(1)
        except Exception:
            break

    # Collect description text
    desc = ""
    for sel in ["[data-test-id*='description']", "p", "[class*='description']"]:
        try:
            els = page.query_selector_all(sel)
            for el in els[:5]:
                t = el.inner_text().strip()
                if len(t) > 60:
                    desc = t[:600]
                    break
            if desc:
                break
        except Exception:
            pass

    # Collect links
    exercises, videos, articles = [], [], []
    seen = set()
    try:
        links = page.query_selector_all("a[href]")
        for link in links:
            try:
                href = link.get_attribute("href") or ""
                title = link.inner_text().strip()
                if not title or not href or href in seen:
                    continue
                seen.add(href)
                full = href if href.startswith("http") else f"{BASE_URL}{href}"
                if "/e/" in href:
                    exercises.append({"title": title, "url": full, "type": "exercise"})
                elif "/v/" in href:
                    videos.append({"title": title, "url": full, "type": "video"})
                elif "/a/" in href:
                    articles.append({"title": title, "url": full, "type": "article"})
            except Exception:
                continue
    except Exception:
        pass

    print(f"  exercises={len(exercises)} videos={len(videos)} desc={len(desc)} chars", flush=True)
    for ex in exercises[:5]:
        print(f"    [ex] {ex['title']}")

    return {
        "code": code,
        "description": desc,
        "exercises": exercises,
        "videos": videos,
        "articles": articles,
    }


def main():
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-dev-shm-usage", "--no-sandbox"])
        ctx = browser.new_context(ignore_https_errors=True)
        page = ctx.new_page()
        # Suppress page-level JS errors that would crash the Node subprocess
        page.on("pageerror", lambda e: None)
        page.on("console", lambda m: None)
        page.set_default_timeout(30000)

        for code in STANDARDS:
            result = scrape_standard(page, code)
            if result:
                results.append(result)
            time.sleep(2)

        browser.close()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved {len(results)} standards to {OUTPUT}")

    # Summary
    for r in results:
        print(f"  {r['code']}: {len(r['exercises'])} exercises, {len(r['videos'])} videos")


if __name__ == "__main__":
    main()
