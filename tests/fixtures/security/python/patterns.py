# Corpus: comprobaciones estructurales en Python.
import hashlib
import random
import secrets
import yaml
import jwt
import requests

DB_PASSWORD = "Sup3r-S3cret-2024"  # expect: SEC-SECRET
PASSWORD_FIELD = "password"
API_KEY = "${API_KEY}"
TOKEN_URL = "https://auth.example.com/token"
aws_key = "AKIAABCDEFGHIJKLMNOP"  # expect: SEC-SECRET


def checksum(data):
    return hashlib.sha256(data).hexdigest()


def legacy_etag(data):
    return hashlib.md5(data, usedforsecurity=False).hexdigest()


def password_hash(password):
    return hashlib.md5(password.encode()).hexdigest()  # expect: SEC-WEAKHASH


def new_reset_token():
    reset_token = random.randint(100000, 999999)  # expect: SEC-WEAKRANDOM
    good_token = secrets.token_urlsafe(32)
    jitter = random.random()
    return reset_token, good_token, jitter


def load_config(path):
    with open(path) as handle:
        safe = yaml.safe_load(handle)
    with open(path) as handle:
        unsafe = yaml.load(handle)  # expect: SEC-UNSAFE-DESER-API
    return safe, unsafe


def call_partner():
    requests.get("https://partner.example.com", timeout=5, verify=False)  # expect: SEC-TLS


def read_token(token, key):
    jwt.decode(token, key, algorithms=["HS256"])
    return jwt.decode(token, options={"verify_signature": False})  # expect: SEC-JWT


def swallow():
    try:
        risky()
    except ValueError:  # expect: BUG-EMPTY-CATCH
        pass
    try:
        risky()
    except Exception:
        log_error()
        raise


def collect(item, bucket=[]):  # expect: BUG-MUTABLE-DEFAULT
    bucket.append(item)
    return bucket


def status_ok(status):
    if status is None:
        return False
    return status is "OK"  # expect: BUG-IS-LITERAL


def risky():
    pass


def log_error():
    pass
