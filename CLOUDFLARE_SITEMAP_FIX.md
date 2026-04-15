# Cloudflare — Sitemap Fix Checklist for kolo.xyz

**Problem:** Google Search Console reports "Couldn't fetch" for kolo.xyz/sitemap.xml
**Goal:** Make sure Googlebot can fetch the sitemap with correct content-type

---

## What to check (in order)

### 1. Is the Worker route catching /sitemap.xml?

Go to **Cloudflare Dashboard → Workers & Pages → kolo-proxy → Triggers (Routes)**

Check if there's a route like `kolo.xyz/sitemap.xml` or `kolo.xyz/*` assigned to the worker.

- **If `kolo.xyz/*` is a route** → the worker intercepts ALL requests to kolo.xyz, including /sitemap.xml. This means the worker's `handleSitemap()` function runs, which tries to fetch `https://kolo.xyz/sitemap.xml` again — **this creates an infinite loop**. The worker is fetching from itself.
- **If only `kolo-proxy.ek-3ff.workers.dev/*`** → the worker is NOT intercepting kolo.xyz traffic. The sitemap is served directly by Webflow. The problem is likely Webflow's content-type.

**Action needed:**
- If the worker IS on kolo.xyz routes: change the sitemap fetch URL inside the worker from `https://kolo.xyz/sitemap.xml` to the **Webflow origin URL directly** (see step 4)
- If the worker is NOT on kolo.xyz routes: skip to step 2

### 2. Check kolo.xyz DNS / Proxy settings

Go to **Cloudflare Dashboard → DNS**

- Is kolo.xyz proxied through Cloudflare (orange cloud)? Or DNS-only (gray cloud)?
- If **proxied (orange cloud)**: Cloudflare sits between Googlebot and Webflow. Check if any Page Rules, Cache Rules, or WAF rules block /sitemap.xml
- If **DNS-only (gray)**: Cloudflare doesn't touch the traffic. Problem is purely Webflow-side.

### 3. Test the sitemap URL

Run these checks:

```
# Check response code and content-type
curl -I https://kolo.xyz/sitemap.xml

# Expected:
# HTTP/2 200
# content-type: application/xml  (or text/xml)

# If you see:
# content-type: application/rss+xml  → Webflow bug, needs fixing
# HTTP 301/302 redirect → follow the redirect, check final URL
# HTTP 403/404 → something is blocking it
```

```
# Check what Googlebot sees (simulate its user agent)
curl -A "Googlebot" https://kolo.xyz/sitemap.xml | head -20
```

```
# Check the actual content
curl https://kolo.xyz/sitemap.xml | head -50
```

### 4. Fix the content-type issue

Webflow serves sitemaps with `content-type: application/rss+xml` instead of `application/xml`. Some Google crawlers reject this.

**Option A — Cloudflare Transform Rule (recommended, no worker needed):**

Go to **Rules → Transform Rules → Modify Response Header**

- **When:** URI Path equals `/sitemap.xml`
- **Then:** Set response header `Content-Type` to `application/xml; charset=UTF-8`
- Save and deploy

**Option B — Use the Worker (if it's already on kolo.xyz routes):**

The worker code already does this, but fix the origin fetch to avoid loops:

Change line 93 in the worker from:
```javascript
const webflowResp = await fetch('https://kolo.xyz/sitemap.xml', {
```
To the direct Webflow origin (find your Webflow site's actual hosting URL):
```javascript
const webflowResp = await fetch('https://proxy-ssl.webflow.com/YOUR_WEBFLOW_SITE_ID/sitemap.xml', {
```
Or use the Webflow staging URL. The key is: **don't fetch from kolo.xyz if the worker IS kolo.xyz**.

### 5. Check Cache settings

Go to **Cloudflare Dashboard → Caching → Cache Rules**

- Is /sitemap.xml being cached? If cached with a stale version, Googlebot gets old data
- **Recommended:** Add a cache rule for `/sitemap.xml` with TTL of 1 hour (3600s) or set to "Bypass Cache" temporarily until Google confirms it can fetch

### 6. Check WAF / Bot rules

Go to **Security → WAF** and **Security → Bots**

- Is "Bot Fight Mode" enabled? This can block Googlebot
- Are there any firewall rules that might block requests to /sitemap.xml?
- Check **Security → Events** — filter by URI `/sitemap.xml` to see if any requests were blocked

### 7. Check Page Rules

Go to **Rules → Page Rules**

- Any rules matching `*kolo.xyz/sitemap*` that redirect or block?

---

## After fixing

1. Visit `https://kolo.xyz/sitemap.xml` in browser — should show XML with correct content-type
2. Test with curl: `curl -I https://kolo.xyz/sitemap.xml` — verify `content-type: application/xml`
3. Go to **Google Search Console → Sitemaps → Resubmit** `https://kolo.xyz/sitemap.xml`
4. Wait 24-48 hours for Google to re-fetch

---

## Quick summary for the Cloudflare person

> Google can't fetch our sitemap at kolo.xyz/sitemap.xml. Please check:
> 1. Is there a Worker route on kolo.xyz that might create a fetch loop for /sitemap.xml?
> 2. Is the content-type correct? (should be application/xml, not application/rss+xml)
> 3. Are any WAF, bot, or cache rules blocking or serving stale content to Googlebot?
> 4. Add a Transform Rule to set content-type to application/xml for /sitemap.xml if needed
