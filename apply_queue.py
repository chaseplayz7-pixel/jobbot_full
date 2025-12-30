import sqlite3
from typing import Dict, List

DB = 'review_queue.db'

def init_db(path=DB):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        title TEXT,
        company TEXT,
        location TEXT,
        link TEXT UNIQUE,
        scraped_at TEXT,
        status TEXT DEFAULT 'new'
    )
    ''')
    conn.commit()
    conn.close()

def add_job(job: Dict, path=DB):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    try:
        cur.execute('INSERT OR IGNORE INTO queue (source,title,company,location,link,scraped_at) VALUES (?,?,?,?,?,datetime("now"))',
                    (job.get('source'), job.get('title'), job.get('company'), job.get('location',''), job.get('link')))
        conn.commit()
    finally:
        conn.close()

def list_jobs(status='new', path=DB) -> List[Dict]:
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute('SELECT id,source,title,company,location,link,scraped_at,status FROM queue WHERE status=? ORDER BY scraped_at DESC', (status,))
    rows = cur.fetchall()
    conn.close()
    keys = ['id','source','title','company','location','link','scraped_at','status']
    return [dict(zip(keys,row)) for row in rows]

def mark_reviewed(job_id: int, path=DB):
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute('UPDATE queue SET status=? WHERE id=?', ('reviewed', job_id))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print('Initialized review queue DB at', DB)
