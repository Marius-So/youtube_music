from flask import Flask, send_file, render_template
from threading import Thread
import os

app = Flask('')


@app.route('/')
def index():
  return render_template('index.html')


@app.route('/download')
def download_file():
  path = "1live_link_match.csv"
  return send_file(path, as_attachment=True)


def run():
  app.run(host='0.0.0.0', port=8080)


def keep_alive():
  t = Thread(target=run)
  t.start()
