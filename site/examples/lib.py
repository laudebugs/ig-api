"""Minimal Graph client shared by examples/ (requires: pip install requests).

Env: GRAPH_HOST (default https://graph.facebook.com), GRAPH_VERSION (default v25.0),
     IG_USER_ID, ACCESS_TOKEN
"""
import os
import random
import time

import requests

BASE = f"{os.environ.get('GRAPH_HOST', 'https://graph.facebook.com')}/{os.environ.get('GRAPH_VERSION', 'v25.0')}"
TOKEN = os.environ.get("ACCESS_TOKEN", "")
IG_USER_ID = os.environ.get("IG_USER_ID", "")


class GraphError(RuntimeError):
    def __init__(self, method, path, error, status):
        self.code = (error or {}).get("code")
        self.subcode = (error or {}).get("error_subcode")
        self.fbtrace_id = (error or {}).get("fbtrace_id")
        super().__init__(f"{method} {path} -> {self.code}: {(error or {}).get('message', status)}")


def gget(path, params=None):
    r = requests.get(f"{BASE}{path}", headers={"Authorization": f"Bearer {TOKEN}"},
                     params=params or {}, timeout=30)
    data = r.json()
    if r.status_code != 200:
        raise GraphError("GET", path, data.get("error"), r.status_code)
    return data


def gpost(path, data=None):
    payload = dict(data or {})
    payload["access_token"] = TOKEN
    r = requests.post(f"{BASE}{path}", data=payload, timeout=60)
    body = r.json()
    if r.status_code != 200:
        raise GraphError("POST", path, body.get("error"), r.status_code)
    return body


def gpost_json(path, payload):
    r = requests.post(f"{BASE}{path}", headers={"Authorization": f"Bearer {TOKEN}"},
                      json=payload, timeout=30)
    body = r.json()
    if r.status_code != 200:
        raise GraphError("POST", path, body.get("error"), r.status_code)
    return body


RETRYABLE = {1, 2, 4, 17, 32}


def with_retry(fn, tries=5):
    delay = 1.0
    for i in range(tries):
        try:
            return fn()
        except GraphError as e:
            if i == tries - 1 or (e.code is not None and e.code not in RETRYABLE):
                raise
            time.sleep(delay + random.uniform(0, 0.25))
            delay *= 2
