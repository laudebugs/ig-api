# Insights — Instagram Graph API

> Generated: 2026-10-13 · Base: `https://graph.facebook.com/v25.0` · Requires: `instagram_manage_insights`

Metrics change across Graph versions; treat metric names as versioned. If a metric returns error 100, check the metric list for your `GRAPH_VERSION` in Meta for Developers.

## Account insights

```bash
curl "https://graph.facebook.com/v25.0/17841400008460056/insights?metric=reach,views,accounts_engaged&period=day&access_token=EAAB..."
```

```json
{
  "data": [
    { "name": "reach", "period": "day", "values": [{ "value": 1204, "end_time": "2026-10-13T07:00:00+0000" }], "id": "17841400008460056/insights/reach/day" }
  ]
}
```

Date range with Unix timestamps:

```bash
curl "https://graph.facebook.com/v25.0/17841400008460056/insights?metric=reach&period=day&since=1759276800&until=1759968000&access_token=EAAB..."
```

Common account metrics: `views`, `reach`, `accounts_engaged`, `total_interactions`, `likes`, `comments`, `shares`, `saves`, `profile_links_taps`. Interaction metrics use `period=day`; demographic metrics use `period=lifetime` + `timeframe`. Do not use `impressions` (dropped for v22+), `profile_views`, or `website_clicks` (removed).

## Media insights

```bash
curl "https://graph.facebook.com/v25.0/17987654321098765/insights?metric=views,reach,saved,shares&access_token=EAAB..."
```

Runnable code: [../examples/fetch-insights.ts](../examples/fetch-insights.ts). Media metrics vary by `media_product_type`: feed posts commonly support `views`, `reach`, `saved`, `shares`, `total_interactions`, `likes`, `comments`; Reels add `ig_reels_avg_watch_time` / `ig_reels_video_view_total_time`. There is no `engagement` metric, and `plays` is deprecated — use `views`. Insights are unavailable for media inside carousel albums. Request only metrics valid for that media type or the whole call fails.

## Story insights

Stories expire after 24 hours; fetch insights while the story is live (or via `/{ig-user-id}/stories` then `/{media-id}/insights` with story metrics such as `views`, `reach`, `replies`, `navigation`).

## Agent rules

- Parse `values[].value` defensively: some metrics return objects (breakdowns), not numbers.
- Align `since`/`until` to full days; partial windows truncate silently.
- Cache daily insights; re-polling history rarely changes after 48 hours.
- A single invalid metric fails the request — bisect metric lists on error 100.

Next: [comments-moderation.md](comments-moderation.md) · [errors-and-rate-limits.md](errors-and-rate-limits.md)
