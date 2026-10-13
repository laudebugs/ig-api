"""Publish a single photo via the Graph API (two-step flow).
Generated: 2026-10-13
Env: IG_USER_ID, ACCESS_TOKEN (Page token), GRAPH_HOST, GRAPH_VERSION, IMAGE_URL, CAPTION
Run: python publish-photo.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from lib import IG_USER_ID, gpost


def main():
    container = gpost(f"/{IG_USER_ID}/media", {
        "image_url": os.environ.get("IMAGE_URL", "https://example.com/photo.jpg"),
        "caption": os.environ.get("CAPTION", "Hello from the API #launch"),
    })
    print("Container:", container["id"])

    published = gpost(f"/{IG_USER_ID}/media_publish", {"creation_id": container["id"]})
    print("Published media ID:", published["id"])


if __name__ == "__main__":
    main()
