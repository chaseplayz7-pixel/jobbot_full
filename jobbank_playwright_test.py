from playwright.sync_api import sync_playwright
import csv
from datetime import datetime

KEYWORDS = ["Technical Program Manager","TPM","Program Manager","Data Center","Physical Security","Security Program Manager"]
OUTPUT = 'jobs_results_jobbank.csv'


def matches_keywords(text):
    t = (text or '').lower()
    return any(k.lower() in t for k in KEYWORDS)


def scrape_jobbank(page, limit=100):
    results = []
    q = ' '.join(KEYWORDS)
    url = f'https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={q}&locationstring=Canada'
    page.goto(url)
    page.wait_for_timeout(3500)
    html = page.content()
    # find job posting links in HTML as a fallback
    import re
    hrefs = re.findall(r'href=["\'](/jobsearch/jobposting/[^"\']+)["\']', html)
    anchors = []
    for h in hrefs:
        try:
            anchors.append(h)
        except Exception:
            continue
    seen = set()
    for a in anchors[:limit]:
        try:
            href = a if isinstance(a, str) else a.get_attribute('href')
            if not href:
                continue
            link = page.url.split('/jobsearch')[0] + href if href.startswith('/') else href
            if link in seen:
                continue
            seen.add(link)
            page.goto(link)
            page.wait_for_timeout(1400)
            title = page.query_selector('h1')
            title_t = title.inner_text().strip() if title else ''
            company_el = page.query_selector('.employer-name')
            company = company_el.inner_text().strip() if company_el else ''
            loc_el = page.query_selector('[itemprop="jobLocation"]')
            loc = loc_el.inner_text().strip() if loc_el else ''
            desc_el = page.query_selector('[itemprop="description"]')
            desc = desc_el.inner_text().strip() if desc_el else ''
            if matches_keywords(title_t + ' ' + desc):
                results.append({'source':'JobBank','title':title_t,'company':company,'location':loc,'link':link,'description':desc[:2000]})
        except Exception as e:
            print('jobbank item error', e)
            continue
    return results


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        jobs = scrape_jobbank(page, limit=100)
        if jobs:
            keys = ['source','title','company','location','link','description']
            with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for r in jobs:
                    writer.writerow(r)
            print(f'Saved {len(jobs)} records to {OUTPUT} at {datetime.utcnow().isoformat()}')
        else:
            print('No jobbank results')
        browser.close()

if __name__ == '__main__':
    main()
