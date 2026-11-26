# Corpus: Flask. Cada línea con "expect:" debe producir exactamente esos hallazgos; el resto, ninguno.
import os
import shlex
import sqlite3
import subprocess
import pickle
import json
import requests
from flask import Flask, request, redirect, render_template_string, render_template, send_from_directory
from markupsafe import escape
from werkzeug.utils import secure_filename

app = Flask(__name__)
ALLOWED = {"asc", "desc"}


def run_sql(conn, sql):
    return conn.execute(sql)  # se informa en la llamada, no aquí


@app.route("/users")
def users():
    name = request.args.get("name", "")
    conn = sqlite3.connect("app.db")
    conn.execute("SELECT * FROM users WHERE name = ?", (name,))
    conn.execute("SELECT * FROM users WHERE name = '%s'" % name)  # expect: SEC-SQLI
    query = "SELECT * FROM users WHERE name = '{}'".format(name)
    cur = conn.cursor()
    cur.execute(query)  # expect: SEC-SQLI
    order = request.args.get("order", "asc")
    if order not in ALLOWED:
        order = "asc"
    run_sql(conn, f"SELECT * FROM users WHERE name = '{name}'")  # expect: SEC-SQLI
    limit = int(request.args.get("limit", 10))
    conn.execute(f"SELECT * FROM users LIMIT {limit}")
    return render_template("users.html", name=name)


@app.route("/ping")
def ping():
    host = request.args["host"]
    subprocess.run(["ping", "-c", "1", host], check=False)
    subprocess.run("ping -c 1 " + shlex.quote(host), shell=True)
    os.system("ping -c 1 " + host)  # expect: SEC-CMDI
    subprocess.check_output(f"nslookup {host}", shell=True)  # expect: SEC-CMDI
    return "ok"


@app.route("/files/<path:name>")
def files(name):
    with open(os.path.join("/srv/data", name)) as handle:  # expect: SEC-PATH
        handle.read()
    open(os.path.join("/srv/data", secure_filename(name))).read()
    return send_from_directory("/srv/data", name)


@app.route("/hello")
def hello():
    who = request.args.get("who", "")
    if who:
        return "<h1>Hola " + who + "</h1>"  # expect: SEC-XSS
    return "<h1>Hola " + str(escape(request.args.get("x", ""))) + "</h1>"


@app.route("/fetch", methods=["POST"])
def fetch():
    url = request.get_json()["url"]
    requests.get(url, timeout=5)  # expect: SEC-SSRF
    requests.get("https://api.internal/status", timeout=5)
    return redirect(request.args.get("next", "/"))  # expect: SEC-REDIRECT


@app.route("/render")
def render():
    return render_template_string(request.args.get("tpl", ""))  # expect: SEC-SSTI


@app.route("/state", methods=["POST"])
def state():
    data = request.get_data()
    json.loads(data)
    return str(pickle.loads(data))  # expect: SEC-DESER


@app.route("/calc")
def calc():
    expression = request.args.get("e", "1")
    return str(eval(expression))  # expect: SEC-CODEI


def internal_job():
    os.system("rm -rf /tmp/cache")
    subprocess.run("ls -la", shell=True)
    eval("1 + 1")
