"""Reply to an Instagram comment via the Graph API.
Generated: 2026-10-13
Env: ACCESS_TOKEN (Page token), GRAPH_HOST, GRAPH_VERSION, COMMENT_ID, MESSAGE
Run: python reply-to-comment.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from lib import gpost


def main():
    comment_id = os.environ.get("COMMENT_ID", "178700001")
    reply = gpost(f"/{comment_id}/replies", {
        "message": os.environ.get("MESSAGE", "Thanks! More coming Friday."),
    })
    print("Reply comment ID:", reply["id"])


if __name__ == "__main__":
    main()
