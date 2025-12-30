from flask import Flask, render_template, redirect, url_for, request
import apply_queue
import os
from generate_documents import render_resume

app = Flask(__name__)
DB_PATH = 'review_queue.db'


@app.route('/')
def index():
    jobs = apply_queue.list_jobs('new', path=DB_PATH)
    return render_template('index.html', jobs=jobs)


@app.route('/job/<int:job_id>')
def view_job(job_id):
    jobs = apply_queue.list_jobs('new', path=DB_PATH)
    job = next((j for j in jobs if j['id']==job_id), None)
    if not job:
        return redirect(url_for('index'))
    return render_template('job.html', job=job)


@app.route('/job/<int:job_id>/mark', methods=['POST'])
def mark_job(job_id):
    apply_queue.mark_reviewed(job_id, path=DB_PATH)
    return redirect(url_for('index'))


@app.route('/job/<int:job_id>/generate')
def generate_for_job(job_id):
    jobs = apply_queue.list_jobs('new', path=DB_PATH)
    job = next((j for j in jobs if j['id']==job_id), None)
    if not job:
        return redirect(url_for('index'))
    # create a simple tailored summary for the job
    overrides = {
        'summary': f"Targeted resume for {job['title']} at {job['company']}",
        'experience': 'See full experience in attached detailed resume.'
    }
    render_resume(overrides=overrides, out_html=f'resume_job_{job_id}.html', out_pdf=f'resume_job_{job_id}.pdf')
    return redirect(url_for('view_job', job_id=job_id))


if __name__ == '__main__':
    apply_queue.init_db()
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    app.template_folder = template_dir
    app.run(host='127.0.0.1', port=5000, debug=True)
