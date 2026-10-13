"""Fetch account insights and media insights from the Instagram Graph API.
Generated: 2026-10-13
Env: IG_USER_ID, ACCESS_TOKEN (Page token), GRAPH_HOST, GRAPH_VERSION, MEDIA_ID (optional)
Run: python fetch-insights.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from lib import IG_USER_ID, gget


def main():
    account = gget(f"/{IG_USER_ID}/insights",
                   {"metric": "reach,views,accounts_engaged", "period": "day"})
    print("Account insights:", json.dumps(account["data"], indent=2))

    media_id = os.environ.get("MEDIA_ID")
    if media_id:
        media = gget(f"/{media_id}/insights",
                     {"metric": "views,reach,saved,shares"})
        print("Media insights:", json.dumps(media["data"], indent=2))


if __name__ == "__main__":
    main()
