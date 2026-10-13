# FAQ — Instagram Graph API

> Generated: 2026-10-13

**Can I use a personal Instagram account?** No. The Graph API requires a Business or Creator account linked to a Facebook Page.

**Why did publishing fail after creating a container?** Usually the video container was not `FINISHED` yet, the container expired (~24h unpublished), or the asset URL was not publicly fetchable. Poll status first; recreate expired containers. See [media-publishing.md](media-publishing.md).

**Why error 190 on every call?** The token expired, was invalidated (password change, app revocation), or you used a user token where a Page token is required. Re-run [authentication.md](authentication.md).

**Why error 10 even though the user granted permission?** The permission may still need App Review for public data, or the token was minted before the permission was granted. Re-authorize and check `debug_token` scopes.

**Can I message any user who follows the account?** No. You can only reply to users who messaged you (IGSID from webhooks), within the 24-hour window or an approved tag. See [messaging.md](messaging.md).

**Which API version should I use?** The version your Meta app is configured for; this bundle's examples use `v25.0` via `GRAPH_VERSION`. Check Meta's changelog and upgrade before a version's deprecation date.

**Graph API or Instagram Platform API?** This bundle covers the Graph API (Facebook Login, Page-linked). The Instagram Platform API (Instagram Login, `graph.instagram.com`) suits consumer apps without a Page; its endpoints overlap but auth and hosts differ. Do not mix tokens between them.

**How do I test without App Review?** Add test users/accounts with roles on your Meta app; Development mode works for those accounts only.

Back to [README](../README.md) · Machine-readable: [openapi.yaml](../openapi.yaml)
