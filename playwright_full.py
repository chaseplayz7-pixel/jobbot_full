from playwright.sync_api import sync_playwright, Error as PlaywrightError
import csv
import yaml
from datetime import datetime
import time
from proxies import load_proxies, pick_proxy

with open('search_control.yaml','r',encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

KEYWORDS = cfg.get('keywords', [])
OUTPUT = cfg.get('output', {}).get('csv_file', 'jobs_results.csv')
PLAY_CFG = cfg.get('scraping', {})
SOURCES = cfg.get('sources', {})
PROXIES = load_proxies()

import random

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
]

def launch_browser(pw):
    user_agent = random.choice(USER_AGENTS)
    proxy_cfg = None
    if PROXIES:
        picked = pick_proxy(PROXIES)
        if picked:
            proxy_cfg = {k: v for k, v in picked.items() if k in ('server', 'username', 'password')}
    if proxy_cfg:
        browser = pw.chromium.launch(headless=PLAY_CFG.get('headless', True), proxy=proxy_cfg)
    else:
        browser = pw.chromium.launch(headless=PLAY_CFG.get('headless', True))
    context = browser.new_context(user_agent=user_agent)
    return context


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


def scrape_jobbank(page, limit=None):
    if limit is None:
        limit = PLAY_CFG.get('max_jobs_per_source', 50)
    results = []
    q = ' '.join(KEYWORDS)
    url = f'https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={q}&locationstring=Canada'
    print(f'JobBank: Searching for "{q}" at {url}')
    page.goto(url)
    page.wait_for_timeout(2000)
    # Scroll to load more jobs
    for _ in range(3):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
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
            page.wait_for_load_state('domcontentloaded')
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


def scrape_indeed(page, limit=None):
    if limit is None:
        limit = PLAY_CFG.get('max_jobs_per_source', 50)
    results = []
    q = '+'.join(KEYWORDS)
    url = f'https://ca.indeed.com/jobs?q={q}&l=Canada'
    print(f'Indeed: Searching for "{q}" at {url}')
    page.goto(url)
    page.wait_for_timeout(3000)
    check_captcha(page)
    # Scroll to load more jobs
    for _ in range(3):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
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
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_timeout(1200)
            check_captcha(page)
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


def check_captcha(page):
    # Check for common CAPTCHA indicators
    if page.query_selector('iframe[src*="recaptcha"]') or 'captcha' in page.url.lower() or page.query_selector('[class*="captcha"]') or page.query_selector('.captcha'):
        print("CAPTCHA detected! The browser window is open. Please solve the CAPTCHA manually, then press Enter here to continue scraping.")
        input("Press Enter after solving CAPTCHA...")
        return True
    return False


def scrape_linkedin(page, limit=None):
    if limit is None:
        limit = PLAY_CFG.get('max_jobs_per_source', 50)
    results = []
    q = '%20'.join(KEYWORDS)
    url = f'https://www.linkedin.com/jobs/search/?keywords={q}&location=Canada'
    print(f'LinkedIn: Searching for "{q}" at {url}')
    page.goto(url)
    page.wait_for_timeout(3000)
    check_captcha(page)
    # Scroll to load more jobs
    for _ in range(3):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
    cards = page.query_selector_all('li[data-occludable-job-id]')
    print(f'LinkedIn: Found {len(cards)} job cards')
    seen = set()
    for c in cards[:limit]:
        try:
            link_el = c.query_selector('a')
            if not link_el:
                continue
            href = link_el.get_attribute('href')
            if not href or href in seen:
                continue
            seen.add(href)
            link = href if href.startswith('http') else 'https://www.linkedin.com' + href
            title_el = c.query_selector('span[aria-hidden="true"]') or c.query_selector('h3')
            title = title_el.inner_text.strip() if title_el else ''
            company_el = c.query_selector('.job-search-card__company-name')
            company = company_el.inner_text.strip() if company_el else ''
            loc_el = c.query_selector('.job-search-card__location')
            loc = loc_el.inner_text.strip() if loc_el else ''
            desc_el = c.query_selector('.job-search-card__description')
            desc = desc_el.inner_text.strip() if desc_el else ''
            if matches_keywords(title + ' ' + company + ' ' + desc):
                results.append({'source':'LinkedIn','title':title,'company':company,'location':loc,'link':link,'description':desc[:2000]})
                print(f'LinkedIn: Added job "{title}" by {company}')
            else:
                print(f'LinkedIn: Skipped job "{title}" - no keyword match')
        except Exception as e:
            print('linkedin item error', e)
            continue
    print(f'LinkedIn: Total results: {len(results)}')
    return results


def scrape_glassdoor(page, limit=None):
    if limit is None:
        limit = PLAY_CFG.get('max_jobs_per_source', 50)
    results = []
    q = ' '.join(KEYWORDS)
    url = f'https://www.glassdoor.com/Job/jobs.htm?sc.keyword={q}'
    print(f'Glassdoor: Searching for "{q}" at {url}')
    page.goto(url)
    page.wait_for_timeout(3000)
    check_captcha(page)
    # Scroll to load more jobs
    for _ in range(3):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
    cards = page.query_selector_all('a[href*="/job-listing/"]')
    print(f'Glassdoor: Found {len(cards)} job cards')
    seen = set()
    for c in cards[:limit]:
        try:
            link_el = c.query_selector('a')
            if not link_el:
                continue
            href = link_el.get_attribute('href')
            if not href:
                continue
            link = 'https://www.glassdoor.com' + href if href.startswith('/') else href
            if link in seen:
                continue
            seen.add(link)
            title = link_el.inner_text.strip()
            company_el = c.query_selector('span.css-1qg0z0e') or c.query_selector('.job-search-1oeuq0e')
            company = company_el.inner_text.strip() if company_el else ''
            loc_el = c.query_selector('span.css-1ik5rs0')
            loc = loc_el.inner_text.strip() if loc_el else ''
            desc_el = c.query_selector('.jobDescriptionContent')
            desc = desc_el.inner_text.strip() if desc_el else ''
            if matches_keywords(title + ' ' + desc):
                results.append({'source':'Glassdoor','title':title,'company':company,'location':loc,'link':link,'description':desc[:2000]})
                print(f'Glassdoor: Added job "{title}" by {company}')
            else:
                print(f'Glassdoor: Skipped job "{title}" - no keyword match')
        except Exception as e:
            print('glassdoor item error', e)
            continue
    print(f'Glassdoor: Total results: {len(results)}')
    return results


def scrape_google_jobs(page, limit=None):
    if limit is None:
        limit = PLAY_CFG.get('max_jobs_per_source', 50)
    results = []
    q = '+'.join(KEYWORDS)
    url = f'https://www.google.com/search?ibp=htl;jobs&q={q}'
    print(f'Google Jobs: Searching for "{q}" at {url}')
    page.goto(url)
    page.wait_for_timeout(3000)
    check_captcha(page)
    # Scroll to load more jobs
    for _ in range(3):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
    # Google Jobs specific: jobs are in the pane
    jobs = page.query_selector_all('.gws-plugins-horizon-jobs__job') or page.query_selector_all('[data-ved*="job"]')
    print(f'Google Jobs: Found {len(jobs)} job entries')
    seen = set()
    for j in jobs[:limit]:
        try:
            title_el = j.query_selector('h3')
            title = title_el.inner_text().strip() if title_el else ''
            company_el = j.query_selector('.vNEEBe')
            company = company_el.inner_text().strip() if company_el else ''
            loc_el = j.query_selector('.Qk80Jf')
            loc = loc_el.inner_text().strip() if loc_el else ''
            link_el = j.query_selector('a')
            link = link_el.get_attribute('href') if link_el else ''
            desc_el = j.query_selector('.HBvzbc')
            desc = desc_el.inner_text().strip() if desc_el else ''
            if link and link not in seen and matches_keywords(title + ' ' + desc):
                seen.add(link)
                results.append({'source':'Google Jobs','title':title,'company':company,'location':loc,'link':link,'description':desc[:2000]})
                print(f'Google Jobs: Added job "{title}" by {company}')
            else:
                print(f'Google Jobs: Skipped job "{title}" - no keyword match or duplicate')
        except Exception as e:
            print('google jobs item error', e)
            continue
    print(f'Google Jobs: Total results: {len(results)}')
    return results


def scrape_monster(page, limit=None):
    if limit is None:
        limit = PLAY_CFG.get('max_jobs_per_source', 50)
    results = []
    q = '+'.join(KEYWORDS)
    url = f'https://www.monster.com/jobs/search?q={q}&where=Canada'
    print(f'Monster: Searching for "{q}" at {url}')
    page.goto(url)
    page.wait_for_timeout(3000)
    check_captcha(page)
    # Scroll to load more jobs
    for _ in range(3):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
    cards = page.query_selector_all('.job-card')
    print(f'Monster: Found {len(cards)} job cards')
    seen = set()
    for c in cards[:limit]:
        try:
            link_el = c.query_selector('a[href*="/job/"]')
            if not link_el:
                continue
            href = link_el.get_attribute('href')
            if not href or href in seen:
                continue
            seen.add(href)
            link = 'https://www.monster.com' + href if href.startswith('/') else href
            title_el = c.query_selector('h3')
            title = title_el.inner_text.strip() if title_el else ''
            company_el = c.query_selector('.job-card__company-name')
            company = company_el.inner_text.strip() if company_el else ''
            loc_el = c.query_selector('.job-card__location')
            loc = loc_el.inner_text.strip() if loc_el else ''
            desc_el = c.query_selector('.job-card__description')
            desc = desc_el.inner_text.strip() if desc_el else ''
            if matches_keywords(title + ' ' + company + ' ' + desc):
                results.append({'source':'Monster','title':title,'company':company,'location':loc,'link':link,'description':desc[:2000]})
                print(f'Monster: Added job "{title}" by {company}')
            else:
                print(f'Monster: Skipped job "{title}" - no keyword match')
        except Exception as e:
            print('monster item error', e)
            continue
    print(f'Monster: Total results: {len(results)}')
    return results


def scrape_ziprecruiter(page, limit=None):
    if limit is None:
        limit = PLAY_CFG.get('max_jobs_per_source', 50)
    results = []
    q = '+'.join(KEYWORDS)
    url = f'https://www.ziprecruiter.com/candidate/search?search={q}&location=Canada'
    print(f'ZipRecruiter: Searching for "{q}" at {url}')
    page.goto(url)
    page.wait_for_timeout(3000)
    check_captcha(page)
    # Scroll to load more jobs
    for _ in range(3):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
    cards = page.query_selector_all('.job_result')
    print(f'ZipRecruiter: Found {len(cards)} job cards')
    seen = set()
    for c in cards[:limit]:
        try:
            link_el = c.query_selector('a[href*="/job/"]')
            if not link_el:
                continue
            href = link_el.get_attribute('href')
            if not href or href in seen:
                continue
            seen.add(href)
            link = 'https://www.ziprecruiter.com' + href if href.startswith('/') else href
            title_el = c.query_selector('h2')
            title = title_el.inner_text.strip() if title_el else ''
            company_el = c.query_selector('.company_name')
            company = company_el.inner_text.strip() if company_el else ''
            loc_el = c.query_selector('.location')
            loc = loc_el.inner_text.strip() if loc_el else ''
            desc_el = c.query_selector('.job_snippet')
            desc = desc_el.inner_text.strip() if desc_el else ''
            if matches_keywords(title + ' ' + company + ' ' + desc):
                results.append({'source':'ZipRecruiter','title':title,'company':company,'location':loc,'link':link,'description':desc[:2000]})
                print(f'ZipRecruiter: Added job "{title}" by {company}')
            else:
                print(f'ZipRecruiter: Skipped job "{title}" - no keyword match')
        except Exception as e:
            print('ziprecruiter item error', e)
            continue
    print(f'ZipRecruiter: Total results: {len(results)}')
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
            context = launch_browser(p)
            try:
                page = context.new_page()
                page.set_default_navigation_timeout(60000)
                page.set_default_timeout(60000)
                res = scrape_jobbank(page, limit=PLAY_CFG.get('max_jobs_per_source', 50))
                return res
            finally:
                try:
                    context.close()
                except Exception:
                    pass

        def run_indeed():
            context = launch_browser(p)
            try:
                page = context.new_page()
                page.set_default_navigation_timeout(60000)
                page.set_default_timeout(60000)
                res = scrape_indeed(page, limit=PLAY_CFG.get('max_jobs_per_source', 50))
                return res
            finally:
                try:
                    context.close()
                except Exception:
                    pass

        def run_linkedin():
            context = launch_browser(p)
            try:
                page = context.new_page()
                page.set_default_navigation_timeout(60000)
                page.set_default_timeout(60000)
                res = scrape_linkedin(page, limit=PLAY_CFG.get('max_jobs_per_source', 50))
                return res
            finally:
                try:
                    context.close()
                except Exception:
                    pass

        def run_glassdoor():
            context = launch_browser(p)
            try:
                page = context.new_page()
                page.set_default_navigation_timeout(60000)
                page.set_default_timeout(60000)
                res = scrape_glassdoor(page, limit=PLAY_CFG.get('max_jobs_per_source', 50))
                return res
            finally:
                try:
                    context.close()
                except Exception:
                    pass

        def run_google_jobs():
            context = launch_browser(p)
            try:
                page = context.new_page()
                page.set_default_navigation_timeout(60000)
                page.set_default_timeout(60000)
                res = scrape_google_jobs(page, limit=PLAY_CFG.get('max_jobs_per_source', 50))
                return res
            finally:
                try:
                    context.close()
                except Exception:
                    pass

        def run_monster():
            context = launch_browser(p)
            try:
                page = context.new_page()
                page.set_default_navigation_timeout(60000)
                page.set_default_timeout(60000)
                res = scrape_monster(page, limit=PLAY_CFG.get('max_jobs_per_source', 50))
                return res
            finally:
                try:
                    context.close()
                except Exception:
                    pass

        def run_ziprecruiter():
            context = launch_browser(p)
            try:
                page = context.new_page()
                page.set_default_navigation_timeout(60000)
                page.set_default_timeout(60000)
                res = scrape_ziprecruiter(page, limit=PLAY_CFG.get('max_jobs_per_source', 50))
                return res
            finally:
                try:
                    context.close()
                except Exception:
                    pass

        try:
            if SOURCES.get('jobbank', True):
                all_results.extend(run_with_retries(run_jobbank, attempts=PLAY_CFG.get('retries', 2), backoff=3) or [])
        except Exception as e:
            print('jobbank scrape failed after retries', e)

        try:
            if SOURCES.get('indeed', True):
                all_results.extend(run_with_retries(run_indeed, attempts=PLAY_CFG.get('retries', 2), backoff=3) or [])
        except Exception as e:
            print('indeed scrape failed after retries', e)

        try:
            if SOURCES.get('linkedin', False):
                all_results.extend(run_with_retries(run_linkedin, attempts=PLAY_CFG.get('retries', 2), backoff=3) or [])
        except Exception as e:
            print('linkedin scrape failed after retries', e)

        try:
            if SOURCES.get('glassdoor', False):
                all_results.extend(run_with_retries(run_glassdoor, attempts=PLAY_CFG.get('retries', 2), backoff=3) or [])
        except Exception as e:
            print('glassdoor scrape failed after retries', e)

        try:
            if SOURCES.get('google_jobs', False):
                all_results.extend(run_with_retries(run_google_jobs, attempts=PLAY_CFG.get('retries', 2), backoff=3) or [])
        except Exception as e:
            print('google_jobs scrape failed after retries', e)

        try:
            if SOURCES.get('monster', False):
                all_results.extend(run_with_retries(run_monster, attempts=PLAY_CFG.get('retries', 2), backoff=3) or [])
        except Exception as e:
            print('monster scrape failed after retries', e)

        try:
            if SOURCES.get('ziprecruiter', False):
                all_results.extend(run_with_retries(run_ziprecruiter, attempts=PLAY_CFG.get('retries', 2), backoff=3) or [])
        except Exception as e:
            print('ziprecruiter scrape failed after retries', e)

        # company ATS
        if SOURCES.get('company_ats', True):
            for c in cfg.get('target_companies', []):
                def make_company_run(company, url):
                    def _run():
                        context = launch_browser(p)
                        try:
                            page = context.new_page()
                            page.set_default_navigation_timeout(60000)
                            page.set_default_timeout(60000)
                            return scrape_company_ats(page, company, url)
                        finally:
                            try:
                                context.close()
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
            # Always create the file with headers for CI upload
            keys = ['source','title','company','location','link','description']
            with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
            print(f'No results found, created empty {OUTPUT} at {datetime.utcnow().isoformat()}')

if __name__ == '__main__':
    main()
