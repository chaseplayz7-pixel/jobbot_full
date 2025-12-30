from playwright.sync_api import sync_playwright
import os
import csv

KEYWORDS = os.environ.get('KEYWORDS','Technical Program Manager,TPM,Program Manager,Data Center,Physical Security').split(',')
OUTPUT = os.environ.get('OUTPUT','jobs_results_apify.csv')


def matches_keywords(text):
    t = (text or '').lower()
    return any(k.lower() in t for k in KEYWORDS)


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # minimal example: visit JobBank
        page.goto('https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring=' + '+'.join(KEYWORDS) + '&locationstring=Canada')
        page.wait_for_timeout(2000)
        anchors = page.query_selector_all('a[href*="/jobsearch/jobposting/"]')
        results = []
        for a in anchors[:50]:
            try:
                href = a.get_attribute('href')
                link = 'https://www.jobbank.gc.ca' + href
                page.goto(link)
                page.wait_for_timeout(1000)
                title = page.query_selector('h1')
                title_t = title.inner_text().strip() if title else ''
                desc = page.inner_text('body')
                if matches_keywords(title_t + ' ' + desc):
                    results.append({'title':title_t,'link':link})
            except Exception:
                continue
        # write CSV
        with open(OUTPUT,'w',newline='',encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['title','link'])
            writer.writeheader()
            for r in results:
                writer.writerow(r)
        browser.close()

if __name__ == '__main__':
    run()
