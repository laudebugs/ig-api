"""Publish a Reel: create a REELS container, poll until FINISHED, then publish.
Generated: 2026-10-13
Env: IG_USER_ID, ACCESS_TOKEN (Page token), GRAPH_HOST, GRAPH_VERSION, VIDEO_URL, CAPTION
Run: python publish-reel.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from lib import IG_USER_ID, gget, gpost


def wait_finished(container_id, tries=120):
    for _ in range(tries):
        s = gget(f"/{container_id}", {"fields": "status_code,status"})
        print("Status:", s["status_code"])
        if s["status_code"] == "FINISHED":
            return
        if s["status_code"] in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Container {s['status_code']}: {s.get('status', 'unknown')}")
        time.sleep(5)
    raise TimeoutError("timed out waiting for FINISHED")


def main():
    container = gpost(f"/{IG_USER_ID}/media", {
        "media_type": "REELS",
        "video_url": os.environ.get("VIDEO_URL", "https://example.com/reel.mp4"),
        "caption": os.environ.get("CAPTION", "New reel"),
        "share_to_feed": "true",
    })
    print("Container:", container["id"])
    wait_finished(container["id"])
    published = gpost(f"/{IG_USER_ID}/media_publish", {"creation_id": container["id"]})
    print("Published Reel media ID:", published["id"])


if __name__ == "__main__":
    main()
