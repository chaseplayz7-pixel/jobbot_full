import urllib.request
import urllib.parse
import ssl
import re
import csv
from datetime import datetime

cfg = {
    'keywords': ["Technical Program Manager","TPM","Program Manager","Data Center","Physical Security","Security Program Manager"],
    'visa_keywords': ["global talent stream","gts","lmia","visa sponsorship","work permit"],
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
    'max_per_source': 50,
    'output_csv': 'jobs_results_stdlib.csv'
}

ctx = ssl.create_default_context()

headers = {'User-Agent': cfg['user_agent']}


def fetch(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
        return resp.read().decode(errors='ignore')


def find_links_jobbank(html):
    # find hrefs like /jobsearch/jobposting/\d+
    return re.findall(r'href="(/jobsearch/jobposting/[^"\']+)"', html)


def find_links_indeed(html):
    # find hrefs containing /rc/clk or /pagead
    return re.findall(r'href="(/rc/clk[^"\']+)"', html)


def text_from_html(html):
    # crude: remove scripts/styles and tags
    html = re.sub(r'<(script|style)[\s\S]*?</\1>', ' ', html, flags=re.I)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def detect_visa(text):
    t = text.lower()
    hits = [k for k in cfg['visa_keywords'] if k in t]
    return hits


def jobbank_search():
    base = 'https://www.jobbank.gc.ca'
    q = urllib.parse.quote_plus(' '.join(cfg['keywords']))
    url = f'https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={q}&locationstring=Canada'
    print('Fetching JobBank:', url)
    try:
        html = fetch(url)
    except Exception as e:
        print('JobBank fetch error', e)
        return []
    links = find_links_jobbank(html)
    results = []
    seen = set()
    for href in links[:cfg['max_per_source']]:
        link = base + href
        if link in seen:
            continue
        seen.add(link)
        try:
            page = fetch(link)
            title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', page)
            title = title_match.group(1).strip() if title_match else ''
            company_match = re.search(r'Employer\s*</dt>\s*<dd[^>]*>([^<]+)</dd>', page, flags=re.I)
            if not company_match:
                company_match = re.search(r'"employer-name"[^>]*>([^<]+)</', page, flags=re.I)
            company = company_match.group(1).strip() if company_match else ''
            loc_match = re.search(r'Job Location\s*</dt>\s*<dd[^>]*>([^<]+)</dd>', page, flags=re.I)
            loc = loc_match.group(1).strip() if loc_match else ''
            desc = text_from_html(page)
            visa = detect_visa(desc + ' ' + title)
            results.append({'source':'JobBank','title':title,'company':company,'location':loc,'link':link,'visa_hits':';'.join(visa),'visa_score':len(visa),'description':desc[:2000]})
        except Exception as e:
            print('jobbank item error', e)
            continue
    return results


def indeed_search():
    base = 'https://ca.indeed.com'
    q = urllib.parse.quote_plus(' '.join(cfg['keywords']))
    url = f'{base}/jobs?q={q}&l=Canada&fromage=30'
    print('Fetching Indeed:', url)
    try:
        html = fetch(url)
    except Exception as e:
        print('Indeed fetch error', e)
        return []
    links = find_links_indeed(html)
    results = []
    seen = set()
    for href in links[:cfg['max_per_source']]:
        link = base + href
        if link in seen:
            continue
        seen.add(link)
        try:
            page = fetch(link)
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', page)
            title = title_match.group(1).strip() if title_match else ''
            company_match = re.search(r'"company"[^>]*>([^<]+)</', page, flags=re.I)
            company = company_match.group(1).strip() if company_match else ''
            loc_match = re.search(r'"jobsearch-JobInfoHeader-subtitle"[\s\S]*?<div[^>]*>([^<]+)</div>', page, flags=re.I)
            loc = loc_match.group(1).strip() if loc_match else ''
            desc = text_from_html(page)
            visa = detect_visa(desc + ' ' + title)
            results.append({'source':'Indeed','title':title,'company':company,'location':loc,'link':link,'visa_hits':';'.join(visa),'visa_score':len(visa),'description':desc[:2000]})
        except Exception as e:
            print('indeed item error', e)
            continue
    return results


def main():
    results = []
    results.extend(jobbank_search())
    results.extend(indeed_search())
    if not results:
        print('No results')
        return
    out = cfg['output_csv']
    keys = ['source','title','company','location','link','visa_hits','visa_score','description']
    with open(out, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    print(f'Saved {len(results)} records to {out} at {datetime.utcnow().isoformat()}')

if __name__ == '__main__':
    main()
