from playwright.sync_api import sync_playwright
import csv
from datetime import datetime

KEYWORDS = ["Technical Program Manager","TPM","Program Manager","Data Center","Physical Security","Security Program Manager"]
OUTPUT = 'jobs_results_playwright.csv'


def matches_keywords(text):
    t = (text or '').lower()
    return any(k.lower() in t for k in KEYWORDS)


def scrape_jobbank(page):
    results = []
    q = ' '.join(KEYWORDS)
    url = f'https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={q}&locationstring=Canada'
    page.goto(url)
    page.wait_for_timeout(2000)
    # collect posting links
    anchors = page.query_selector_all('a[href*="/jobsearch/jobposting/"]')
    seen = set()
    for a in anchors:
        try:
            href = a.get_attribute('href')
            if not href:
                continue
            link = page.url.split('/jobsearch')[0] + href if href.startswith('/') else href
            if link in seen:
                continue
            seen.add(link)
            page.goto(link)
            page.wait_for_timeout(1000)
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
            if len(results) >= 200:
                break
        except Exception as e:
            print('jobbank item error', e)
            continue
    return results


def scrape_indeed(page):
    results = []
    q = '+'.join(KEYWORDS)
    url = f'https://ca.indeed.com/jobs?q={q}&l=Canada&fromage=30'
    page.goto(url)
    page.wait_for_timeout(3000)
    # job cards
    cards = page.query_selector_all('a.tapItem')
    if not cards:
        cards = page.query_selector_all('a[href*="/rc/clk"]')
    seen = set()
    for c in cards:
        try:
            href = c.get_attribute('href')
            if not href:
                continue
            link = 'https://ca.indeed.com' + href if href.startswith('/') else href
            if link in seen:
                continue
            seen.add(link)
            page.goto(link)
            page.wait_for_timeout(1200)
            title = page.title()
            company_el = page.query_selector('div.jobsearch-InlineCompanyRating div') or page.query_selector('.icl-u-lg-mr--sm')
            company = company_el.inner_text().strip() if company_el else ''
            loc_el = page.query_selector('.jobsearch-JobInfoHeader-subtitle div')
            loc = loc_el.inner_text().strip() if loc_el else ''
            desc_el = page.query_selector('#jobDescriptionText')
            desc = desc_el.inner_text().strip() if desc_el else ''
            if matches_keywords(title + ' ' + desc):
                results.append({'source':'Indeed','title':title,'company':company,'location':loc,'link':link,'description':desc[:2000]})
            if len(results) >= 200:
                break
        except Exception as e:
            print('indeed item error', e)
            continue
    return results


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        all_results = []
        try:
            all_results.extend(scrape_jobbank(page))
        except Exception as e:
            print('jobbank scrape failed', e)
        try:
            all_results.extend(scrape_indeed(page))
        except Exception as e:
            print('indeed scrape failed', e)
        if all_results:
            keys = ['source','title','company','location','link','description']
            with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for r in all_results:
                    writer.writerow(r)
            print(f'Saved {len(all_results)} records to {OUTPUT} at {datetime.utcnow().isoformat()}')
        else:
            print('No results found by Playwright scraper')
        browser.close()

if __name__ == '__main__':
    main()
