"""Minimal MCP server wrapping the Instagram Graph API tools in mcp/tools.json.

Requires: pip install mcp requests
Env: GRAPH_HOST, GRAPH_VERSION, IG_USER_ID, ACCESS_TOKEN (see examples/lib.py)
Run: python mcp/server.py  (stdio transport for MCP clients)

This is a starter: 14 read/publish/insights/comment/message/hashtag tools.
Extend with carousel, stories, block, conversations, and webhook intake as needed.
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "examples"))
from lib import IG_USER_ID, gget, gpost, gpost_json  # noqa: E402

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    raise SystemExit("pip install mcp  (then rerun with IG_USER_ID + ACCESS_TOKEN set)")

mcp = FastMCP("instagram-graph")


@mcp.tool()
def ig_get_profile(fields: str = "id,username,media_count,followers_count") -> dict:
    """Get the IG user profile."""
    return gget(f"/{IG_USER_ID}", {"fields": fields})


@mcp.tool()
def ig_list_media(fields: str = "id,caption,media_type,media_product_type,permalink,timestamp",
                  limit: int = 25, after: str = "") -> dict:
    """List media on the IG account."""
    params = {"fields": fields, "limit": str(limit)}
    if after:
        params["after"] = after
    return gget(f"/{IG_USER_ID}/media", params)


@mcp.tool()
def ig_create_container(image_url: str = "", video_url: str = "",
                        media_type: str = "", caption: str = "") -> dict:
    """Create a media container (step 1 of publishing). Returns container id."""
    body = {}
    if image_url:
        body["image_url"] = image_url
    if video_url:
        body["video_url"] = video_url
    if media_type:
        body["media_type"] = media_type
    if caption:
        body["caption"] = caption
    return gpost(f"/{IG_USER_ID}/media", body)


@mcp.tool()
def ig_wait_container(container_id: str, timeout_seconds: int = 600) -> dict:
    """Poll a container until FINISHED. Returns final status."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        s = gget(f"/{container_id}", {"fields": "status_code,status"})
        if s["status_code"] in ("FINISHED", "ERROR", "EXPIRED", "PUBLISHED"):
            return s
        time.sleep(5)
    raise TimeoutError(f"container {container_id} not FINISHED within {timeout_seconds}s")


@mcp.tool()
def ig_publish_container(creation_id: str) -> dict:
    """Publish a container (step 2). Returns published media id."""
    return gpost(f"/{IG_USER_ID}/media_publish", {"creation_id": creation_id})


@mcp.tool()
def ig_publishing_quota() -> dict:
    """Read publishing quota usage."""
    return gget(f"/{IG_USER_ID}/content_publishing_limit",
                {"fields": "quota_usage,rate_limit_settings,config"})


@mcp.tool()
def ig_account_insights(metric: str, period: str = "day",
                        since: int = 0, until: int = 0) -> dict:
    """Account insights for a metric list + period + Unix range."""
    params = {"metric": metric, "period": period}
    if since:
        params["since"] = str(since)
    if until:
        params["until"] = str(until)
    return gget(f"/{IG_USER_ID}/insights", params)


@mcp.tool()
def ig_media_insights(media_id: str, metric: str) -> dict:
    """Media insights for one media id."""
    return gget(f"/{media_id}/insights", {"metric": metric})


@mcp.tool()
def ig_list_comments(media_id: str,
                     fields: str = "id,text,username,timestamp,like_count,hidden") -> dict:
    """List comments on a media id."""
    return gget(f"/{media_id}/comments", {"fields": fields})


@mcp.tool()
def ig_reply_comment(comment_id: str, message: str) -> dict:
    """Reply to a comment. Returns reply id."""
    return gpost(f"/{comment_id}/replies", {"message": message})


@mcp.tool()
def ig_hide_comment(comment_id: str, hide: bool) -> dict:
    """Hide (true) or unhide (false) a comment."""
    return gpost(f"/{comment_id}", {"hide": "true" if hide else "false"})


@mcp.tool()
def ig_send_message(igsid: str, text: str) -> dict:
    """Send an Instagram DM to a webhook IGSID (24h window).

    Instagram Login flavor only (graph.instagram.com + IG user ID). With Facebook
    Login, send via POST /{page-id}/messages with the Page token instead.
    """
    return gpost_json(f"/{IG_USER_ID}/messages",
                      {"recipient": {"id": igsid}, "messaging_type": "RESPONSE",
                       "message": {"text": text}})


@mcp.tool()
def ig_hashtag_search(q: str) -> dict:
    """Resolve a hashtag name to a hashtag id."""
    return gget("/ig_hashtag_search", {"user_id": IG_USER_ID, "q": q})


@mcp.tool()
def ig_hashtag_recent(hashtag_id: str, limit: int = 25) -> dict:
    """Recent media for a hashtag id."""
    return gget(f"/{hashtag_id}/recent_media",
                {"user_id": IG_USER_ID,
                 "fields": "id,caption,permalink,timestamp,like_count",
                 "limit": str(limit)})


if __name__ == "__main__":
    mcp.run()
