import requests
from bs4 import BeautifulSoup
try:
    import yaml
except Exception:
    yaml = None
import time
import csv
import re
from urllib.parse import quote_plus, urljoin
import pandas as pd
from datetime import datetime

def _simple_load_config(path: str = 'config.yaml'):
    # Minimal, forgiving YAML-like loader for the specific config fields used by this project.
    cfg = {}
    current_list = None
    last_key = None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for raw in f:
                line = raw.rstrip('\n')
                if not line.strip() or line.strip().startswith('#'):
                    continue
                if ':' in line and not line.lstrip().startswith('-'):
                    parts = line.split(':', 1)
                    key = parts[0].strip()
                    val = parts[1].strip()
                    if val == '':
                        # begin list
                        cfg[key] = []
                        current_list = cfg[key]
                        last_key = key
                    else:
                        # basic scalar parsing
                        if val.lower() in ('true', 'false'):
                            cfg[key] = val.lower() == 'true'
                        else:
                            # remove surrounding quotes
                            cfg[key] = val.strip('"').strip("'")
                        current_list = None
                        last_key = key
                elif line.lstrip().startswith('-') and current_list is not None:
                    item = line.lstrip()[1:].strip().strip('"').strip("'")
                    current_list.append(item)
                else:
                    # unhandled line - ignore
                    continue
    except FileNotFoundError:
        return {}
    return cfg

if yaml:
    with open('config.yaml', 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
else:
    cfg = _simple_load_config('config.yaml')

HEADERS = {'User-Agent': cfg.get('user_agent')}
KEYWORDS = cfg.get('keywords', [])
VISA_KEYWORDS = [k.lower() for k in cfg.get('visa_keywords', [])]
OUTPUT = cfg.get('output_csv', 'jobs_results.csv')
MAX_PER_SOURCE = cfg.get('max_results_per_source', 200)


def detect_visa_signals(text: str):
    text_l = (text or '').lower()
    hits = [k for k in VISA_KEYWORDS if k in text_l]
    return hits, len(hits)


def normalize_location(raw: str):
    if not raw:
        return '', ''
    # crude split: city, province
    parts = [p.strip() for p in raw.split(',') if p.strip()]
    if len(parts) == 1:
        return parts[0], ''
    return parts[0], parts[-1]


def jobbank_search(keywords):
    """Search JobBank (jobbank.gc.ca) - best-effort public scraping."""
    base = 'https://www.jobbank.gc.ca'
    results = []
    q = ' '.join(keywords)
    search_url = f'https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={quote_plus(q)}&locationstring=Canada'
    print('JobBank search:', search_url)
    r = requests.get(search_url, headers=HEADERS, timeout=20)
    if r.status_code != 200:
        print('JobBank fetch failed', r.status_code)
        return results
    soup = BeautifulSoup(r.text, 'lxml')
    # look for links to job posting pages
    for a in soup.select('a[href*="/jobsearch/jobposting/"]'):
        href = a.get('href')
        link = urljoin(base, href)
        title = a.get_text(strip=True)
        if not title:
            continue
        # navigate to posting page
        time.sleep(0.5)
        try:
            r2 = requests.get(link, headers=HEADERS, timeout=20)
            if r2.status_code != 200:
                continue
            s2 = BeautifulSoup(r2.text, 'lxml')
            # crude extraction
            comp = s2.select_one('div.employer-name')
            company = comp.get_text(strip=True) if comp else s2.select_one('a[href*="/employers/"]') and s2.select_one('a[href*="/employers/"]').get_text(strip=True) or ''
            loc_raw = s2.select_one('div[itemprop="jobLocation"]')
            if loc_raw:
                loc = loc_raw.get_text(separator=' ', strip=True)
            else:
                loc = ''
            desc = s2.select_one('div[itemprop="description"]')
            desc_text = desc.get_text(separator=' ', strip=True) if desc else ''
            posted = ''
            post_el = s2.find(text=re.compile(r'Posted on|Date posted', re.I))
            if post_el:
                posted = post_el.strip()
            visa_hits, visa_score = detect_visa_signals(desc_text + ' ' + title)
            city, province = normalize_location(loc)
            results.append({
                'source': 'JobBank',
                'title': title,
                'company': company,
                'location': loc,
                'city': city,
                'province': province,
                'posted': posted,
                'link': link,
                'visa_hits': ';'.join(visa_hits),
                'visa_score': visa_score,
                'description': desc_text[:2000]
            })
            if len(results) >= MAX_PER_SOURCE:
                break
        except Exception as e:
            print('jobbank item error', e)
            continue
    return results


def indeed_search(keywords):
    base = 'https://ca.indeed.com'
    q = '+'.join(keywords)
    search_url = f'{base}/jobs?q={quote_plus(" ".join(keywords))}&l=Canada&fromage=30'
    print('Indeed search:', search_url)
    results = []
    r = requests.get(search_url, headers=HEADERS, timeout=20)
    if r.status_code != 200:
        print('Indeed fetch failed', r.status_code)
        return results
    soup = BeautifulSoup(r.text, 'lxml')
    # job cards often have class 'tapItem' or 'jobTitle'
    cards = soup.select('a[href*="/rc/clk"], a.tapItem')
    if not cards:
        cards = soup.select('div.jobsearch-SerpJobCard')
    for a in cards:
        try:
            href = a.get('href')
            if not href:
                continue
            link = urljoin(base, href)
            title = a.get_text(strip=True)
            parent = a.parent
            # attempt to find company and location nearby
            company = ''
            loc = ''
            # look for nearby company element
            comp = a.find_next(string=True)
            # fallback: attempt to request posting page
            time.sleep(0.5)
            r2 = requests.get(link, headers=HEADERS, timeout=20)
            if r2.status_code != 200:
                continue
            s2 = BeautifulSoup(r2.text, 'lxml')
            company_el = s2.select_one('div.jobsearch-InlineCompanyRating div') or s2.select_one('.company')
            company = company_el.get_text(strip=True) if company_el else ''
            loc_el = s2.select_one('.jobsearch-JobInfoHeader-subtitle div')
            loc = loc_el.get_text(separator=' ', strip=True) if loc_el else ''
            desc = s2.select_one('#jobDescriptionText')
            desc_text = desc.get_text(separator=' ', strip=True) if desc else ''
            visa_hits, visa_score = detect_visa_signals(desc_text + ' ' + title)
            city, province = normalize_location(loc)
            results.append({
                'source': 'Indeed',
                'title': title,
                'company': company,
                'location': loc,
                'city': city,
                'province': province,
                'posted': '',
                'link': link,
                'visa_hits': ';'.join(visa_hits),
                'visa_score': visa_score,
                'description': desc_text[:2000]
            })
            if len(results) >= MAX_PER_SOURCE:
                break
        except Exception as e:
            print('indeed item error', e)
            continue
    return results


def filter_by_keywords(entry, keywords):
    txt = (entry.get('title','') + ' ' + entry.get('description','') + ' ' + entry.get('company','')).lower()
    for k in keywords:
        if k.lower() in txt:
            return True
    return False


def main():
    keywords = KEYWORDS
    provinces = cfg.get('provinces') or []
    results = []

    # JobBank
    jb = jobbank_search(keywords)
    for e in jb:
        if not filter_by_keywords(e, keywords):
            continue
        if not cfg.get('remote_ok') and 'remote' in (e.get('title','') + e.get('description','')).lower():
            continue
        if provinces and e.get('province') and e.get('province') not in provinces:
            continue
        results.append(e)

    # Indeed
    idr = indeed_search(keywords)
    for e in idr:
        if not filter_by_keywords(e, keywords):
            continue
        if not cfg.get('remote_ok') and 'remote' in (e.get('title','') + e.get('description','')).lower():
            continue
        if provinces and e.get('province') and e.get('province') not in provinces:
            continue
        results.append(e)

    # Save CSV
    if results:
        df = pd.DataFrame(results)
        df['scrape_time'] = datetime.utcnow().isoformat()
        df.to_csv(OUTPUT, index=False)
        print(f'Saved {len(df)} records to {OUTPUT}')
    else:
        print('No results found')


if __name__ == '__main__':
    main()
