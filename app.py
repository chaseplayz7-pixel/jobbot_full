from flask import Flask, render_template, request
import csv
import os

app = Flask(__name__)

@app.route('/')
def index():
    csv_file = 'jobs_results.csv'
    jobs = []
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            jobs = list(reader)
    return render_template('index.html', jobs=jobs)

if __name__ == '__main__':
    app.run(debug=True)