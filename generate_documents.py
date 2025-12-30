import yaml
from pathlib import Path
from playwright.sync_api import sync_playwright

with open('config.yaml','r',encoding='utf-8') as f:
    cfg = yaml.safe_load(f)

PROFILE = {
    'name': 'Seun Faniran, PMP',
    'location': 'Dallas–Fort Worth, TX',
    'email': 'waseunfan@gmail.com',
    'phone': '214-732-2927',
    'linkedin': 'https://linkedin.com/in/waseun-fan-3331842a4',
}

TEMPLATE = Path('templates/resume_master.html').read_text(encoding='utf-8')

def render_resume(overrides=None, out_html='resume_output.html', out_pdf='resume_output.pdf'):
    data = PROFILE.copy()
    data.update(overrides or {})
    # minimal placeholders
    data_fields = {
        'summary': data.get('summary','PMP-certified Technical Program Manager with 18+ years...'),
        'skills': data.get('skills','Technical Program Management; Physical Security; Data Centers'),
        'experience': data.get('experience','See detailed resume'),
        'education': data.get('education','BSc, Economics — University of Ibadan\nCertifications: PMP')
    }
    html = TEMPLATE
    for k,v in {**data, **data_fields}.items():
        html = html.replace('{{'+k+'}}', v)
    Path(out_html).write_text(html, encoding='utf-8')

    # render to PDF via Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html)
        page.pdf(path=out_pdf, format='A4')
        browser.close()
    print('Generated', out_html, 'and', out_pdf)

if __name__ == '__main__':
    render_resume()
