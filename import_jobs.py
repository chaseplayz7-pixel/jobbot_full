import csv
import apply_queue

apply_queue.init_db()
count = 0
with open('jobs_results.csv', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        job = {
            'source': r.get('source'),
            'title': r.get('title'),
            'company': r.get('company'),
            'location': r.get('location'),
            'link': r.get('link')
        }
        apply_queue.add_job(job)
        count += 1
print('Imported', count, 'jobs into review_queue.db')
