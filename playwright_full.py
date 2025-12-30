from playwright.sync_api import sync_playwright, Error as PlaywrightError
import csv
import yaml
from datetime import datetime
import time
from proxies import load_proxies, pick_proxy

with open('config.yaml','r',encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

KEYWORDS = cfg.get('keywords')
OUTPUT = cfg.get('output_csv','jobs_results_playwright_full.csv')
PLAY_CFG = cfg.get('playwright', {})
PROXIES = load_proxies()

def launch_browser(pw):
    proxy_cfg = None
    if PROXIES:
        picked = pick_proxy(PROXIES)
        if picked:
            proxy_cfg = {k: v for k, v in picked.items() if k in ('server', 'username', 'password')}
    if proxy_cfg:
        return pw.chromium.launch(headless=PLAY_CFG.get('headless', True), proxy=proxy_cfg)
    return pw.chromium.launch(headless=PLAY_CFG.get('headless', True))


def run_with_retries(action_fn, attempts=2, backoff=2):
    last_exc = None
    for i in range(attempts):
        try:
            return action_fn()
        except PlaywrightError as e:
            last_exc = e
            print(f'Playwright error (attempt {i+1}/{attempts}):', e)
        except Exception as e:
            last_exc = e
            print(f'Error (attempt {i+1}/{attempts}):', e)
        time.sleep(backoff)
    raise last_exc


def matches_keywords(text):
    t = (text or '').lower()
    return any(k.lower() in t for k in KEYWORDS)


def scrape_jobbank(page, limit=50):
    results = []
    q = ' '.join(KEYWORDS)
    url = f'https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={q}&locationstring=Canada'
    print(f'JobBank: Searching for "{q}" at {url}')
    page.goto(url)
    page.wait_for_timeout(2000)
    anchors = page.query_selector_all('a[href*="/jobsearch/jobposting/"]')
    print(f'JobBank: Found {len(anchors)} job links')
    seen = set()
    for a in anchors[:limit]:
        try:
            href = a.get_attribute('href')
            if not href:
                continue
            link = page.url.split('/jobsearch')[0] + href if href.startswith('/') else href
            if link in seen:
                continue
            seen.add(link)
            print(f'JobBank: Visiting {link}')
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
                print(f'JobBank: Added job "{title_t}" by {company}')
            else:
                print(f'JobBank: Skipped job "{title_t}" - no keyword match')
        except Exception as e:
            print('jobbank item error', e)
            continue
    print(f'JobBank: Total results: {len(results)}')
    return results


def scrape_indeed(page, limit=50):
    results = []
    q = '+'.join(KEYWORDS)
    url = f'https://ca.indeed.com/jobs?q={q}&l=Canada'
    print(f'Indeed: Searching for "{q}" at {url}')
    page.goto(url)
    page.wait_for_timeout(3000)
    cards = page.query_selector_all('a.tapItem')
    if not cards:
        cards = page.query_selector_all('a[href*="/rc/clk"]')
    print(f'Indeed: Found {len(cards)} job cards')
    seen = set()
    for c in cards[:limit]:
        try:
            href = c.get_attribute('href')
            if not href:
                continue
            link = 'https://ca.indeed.com' + href if href.startswith('/') else href
            if link in seen:
                continue
            seen.add(link)
            print(f'Indeed: Visiting {link}')
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
                print(f'Indeed: Added job "{title}" by {company}')
            else:
                print(f'Indeed: Skipped job "{title}" - no keyword match')
        except Exception as e:
            print('indeed item error', e)
            continue
    print(f'Indeed: Total results: {len(results)}')
    return results


def scrape_company_ats(page, company, url):
    results = []
    try:
        print('Visiting company careers:', company, url)
        page.goto(url)
        page.wait_for_timeout(2000)
        # attempt to search on the page for keywords (basic text scan)
        page_text = page.inner_text('body')
        if any(k.lower() in page_text.lower() for k in KEYWORDS):
            # try to find links on page
            anchors = page.query_selector_all('a')
            print(f'Company {company}: Found {len(anchors)} links on careers page')
            seen = set()
            job_links = 0
            for a in anchors:
                try:
                    href = a.get_attribute('href')
                    if not href or href.startswith('javascript:'):
                        continue
                    if href in seen:
                        continue
                    seen.add(href)
                    full = href if href.startswith('http') else url.rstrip('/') + '/' + href.lstrip('/')
                    # visit candidate pages with job in path
                    if any(tok in full.lower() for tok in ['job','career','position','opening']):
                        job_links += 1
                        if job_links > 10:  # limit to 10 job links per company
                            continue
                        print(f'Company {company}: Visiting potential job link {full}')
                        page.goto(full)
                        page.wait_for_timeout(1200)
                        txt = page.inner_text('body')
                        if matches_keywords(txt):
                            title = page.title()
                            if 'job' in title.lower() or 'position' in title.lower() or 'career' in title.lower():  # better filter
                                results.append({'source':f'Company:{company}','title':title,'company':company,'location':'','link':full,'description':txt[:2000]})
                                print(f'Company {company}: Added job "{title}"')
                            else:
                                print(f'Company {company}: Skipped page "{title}" - not a job page')
                        else:
                            print(f'Company {company}: Skipped page - no keyword match')
                except Exception:
                    continue
        else:
            print(f'Company {company}: No keywords found on careers page')
    except Exception as e:
        print('company ats error', company, e)
    print(f'Company {company}: Total results: {len(results)}')
    return results


def main():
    with sync_playwright() as p:
        all_results = []
        # run each source in its own browser instance (allows proxy rotation per-run)
        def run_jobbank():
            browser = launch_browser(p)
            try:
                page = browser.new_page()
                page.set_default_navigation_timeout(60000)
                page.set_default_timeout(60000)
                res = scrape_jobbank(page, limit=30)
                return res
            finally:
                try:
                    browser.close()
                except Exception:
                    pass

        def run_indeed():
            browser = launch_browser(p)
            try:
                page = browser.new_page()
                page.set_default_navigation_timeout(60000)
                page.set_default_timeout(60000)
                res = scrape_indeed(page, limit=30)
                return res
            finally:
                try:
                    browser.close()
                except Exception:
                    pass

        try:
            all_results.extend(run_with_retries(run_jobbank, attempts=PLAY_CFG.get('retries', 2), backoff=3) or [])
        except Exception as e:
            print('jobbank scrape failed after retries', e)

        try:
            all_results.extend(run_with_retries(run_indeed, attempts=PLAY_CFG.get('retries', 2), backoff=3) or [])
        except Exception as e:
            print('indeed scrape failed after retries', e)

        # company ATS
        for c in cfg.get('target_companies', []):
            def make_company_run(company, url):
                def _run():
                    browser = launch_browser(p)
                    try:
                        page = browser.new_page()
                        page.set_default_navigation_timeout(60000)
                        page.set_default_timeout(60000)
                        return scrape_company_ats(page, company, url)
                    finally:
                        try:
                            browser.close()
                        except Exception:
                            pass
                return _run

            try:
                runner = make_company_run(c.get('name'), c.get('careers'))
                all_results.extend(run_with_retries(runner, attempts=PLAY_CFG.get('retries', 2), backoff=2) or [])
            except Exception as e:
                print('company scrape failed after retries', c.get('name'), e)
            time.sleep(1)
        if all_results:
            keys = ['source','title','company','location','link','description']
            with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                for r in all_results:
                    writer.writerow(r)
            print(f'Saved {len(all_results)} records to {OUTPUT} at {datetime.utcnow().isoformat()}')
        else:
            print('No results found by Playwright full run')

if __name__ == '__main__':
    main()
