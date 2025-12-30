from playwright.sync_api import Page
from typing import List, Dict

def scrape_workday(page: Page, base_url: str, keywords: List[str], limit=20) -> List[Dict]:
    results = []
    try:
        page.goto(base_url, timeout=30000)
        page.wait_for_timeout(2000)
        # Workday often exposes job links with '/job/' or '/jobs/'
        anchors = page.query_selector_all('a')
        seen = set()
        for a in anchors:
            href = a.get_attribute('href')
            if not href:
                continue
            if '/job/' in href or '/jobs/' in href or 'jobPosting' in href:
                full = href if href.startswith('http') else base_url.rstrip('/') + '/' + href.lstrip('/')
                if full in seen:
                    continue
                seen.add(full)
                page.goto(full)
                page.wait_for_timeout(1000)
                text = page.inner_text('body')
                txt = (text or '').lower()
                if any(k.lower() in txt for k in keywords):
                    title = page.title()
                    results.append({'source':'Workday','title': title, 'company': base_url, 'link': full, 'description': text[:2000]})
                if len(results) >= limit:
                    break
    except Exception:
        pass
    return results


def scrape_greenhouse(page: Page, base_url: str, keywords: List[str], limit=20) -> List[Dict]:
    results = []
    try:
        page.goto(base_url, timeout=30000)
        page.wait_for_timeout(2000)
        # Greenhouse job links commonly contain '/jobs/'
        anchors = page.query_selector_all('a[href*="/jobs/"]')
        seen = set()
        for a in anchors:
            href = a.get_attribute('href')
            if not href:
                continue
            full = href if href.startswith('http') else base_url.rstrip('/') + '/' + href.lstrip('/')
            if full in seen:
                continue
            seen.add(full)
            page.goto(full)
            page.wait_for_timeout(800)
            text = page.inner_text('body')
            if any(k.lower() in (text or '').lower() for k in keywords):
                title = page.title()
                results.append({'source':'Greenhouse','title': title, 'company': base_url, 'link': full, 'description': text[:2000]})
            if len(results) >= limit:
                break
    except Exception:
        pass
    return results


def scrape_lever(page: Page, base_url: str, keywords: List[str], limit=20) -> List[Dict]:
    results = []
    try:
        page.goto(base_url, timeout=30000)
        page.wait_for_timeout(2000)
        anchors = page.query_selector_all('a[href*="/jobs/"]')
        seen = set()
        for a in anchors:
            href = a.get_attribute('href')
            if not href:
                continue
            full = href if href.startswith('http') else base_url.rstrip('/') + '/' + href.lstrip('/')
            if full in seen:
                continue
            seen.add(full)
            page.goto(full)
            page.wait_for_timeout(800)
            text = page.inner_text('body')
            if any(k.lower() in (text or '').lower() for k in keywords):
                title = page.title()
                results.append({'source':'Lever','title': title, 'company': base_url, 'link': full, 'description': text[:2000]})
            if len(results) >= limit:
                break
    except Exception:
        pass
    return results
