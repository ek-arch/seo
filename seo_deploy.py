"""
seo_deploy.py — Deploy programmatic SEO pages to Cloudflare Workers KV
=======================================================================
Handles:
  1. KV namespace management
  2. Bulk upload of HTML pages to KV
  3. Manifest and sitemap upload
  4. Worker binding verification
"""
from __future__ import annotations

import json
import requests
import time
from typing import List, Optional

# Cloudflare config
CF_ACCOUNT_ID = "3ff8191356080bd0d901586d6098dcde"
CF_API_BASE = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}"

KV_NAMESPACE_TITLE = "PSEO_PAGES"


def _headers(api_token: str) -> dict:
    return {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }


# ── KV Namespace Management ──────────────────────────────────────────────────

def list_kv_namespaces(api_token: str) -> list:
    """List all KV namespaces."""
    resp = requests.get(
        f"{CF_API_BASE}/storage/kv/namespaces",
        headers=_headers(api_token),
    )
    data = resp.json()
    return data.get("result", [])


def get_or_create_namespace(api_token: str) -> str:
    """Get existing PSEO_PAGES namespace or create it. Returns namespace ID."""
    namespaces = list_kv_namespaces(api_token)
    for ns in namespaces:
        if ns["title"] == KV_NAMESPACE_TITLE:
            return ns["id"]

    # Create new
    resp = requests.post(
        f"{CF_API_BASE}/storage/kv/namespaces",
        headers=_headers(api_token),
        json={"title": KV_NAMESPACE_TITLE},
    )
    data = resp.json()
    if data.get("success"):
        return data["result"]["id"]
    raise Exception(f"Failed to create KV namespace: {data}")


# ── Upload Pages ──────────────────────────────────────────────────────────────

def upload_page(
    api_token: str,
    namespace_id: str,
    slug: str,
    html: str,
) -> bool:
    """Upload a single page to KV. Key = page:{slug}, Value = HTML."""
    key = f"page:{slug}"
    resp = requests.put(
        f"{CF_API_BASE}/storage/kv/namespaces/{namespace_id}/values/{key}",
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "text/plain",
        },
        data=html.encode("utf-8"),
    )
    return resp.json().get("success", False)


def upload_bulk(
    api_token: str,
    namespace_id: str,
    pages: dict,  # {slug: html_string}
    delay: float = 0.2,
    progress_callback=None,
) -> dict:
    """Upload multiple pages to KV. Returns {uploaded: N, failed: N, errors: [...]}."""
    uploaded = 0
    failed = 0
    errors = []

    total = len(pages)
    for i, (slug, html) in enumerate(pages.items()):
        ok = upload_page(api_token, namespace_id, slug, html)
        if ok:
            uploaded += 1
        else:
            failed += 1
            errors.append(slug)

        if progress_callback:
            progress_callback(i + 1, total)

        time.sleep(delay)

    return {"uploaded": uploaded, "failed": failed, "errors": errors}


def upload_manifest(api_token: str, namespace_id: str, manifest: dict) -> bool:
    """Upload the page manifest to KV."""
    resp = requests.put(
        f"{CF_API_BASE}/storage/kv/namespaces/{namespace_id}/values/manifest",
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        },
        data=json.dumps(manifest, ensure_ascii=False).encode("utf-8"),
    )
    return resp.json().get("success", False)


def upload_sitemap(api_token: str, namespace_id: str, sitemap_xml: str) -> bool:
    """Upload the sitemap fragment to KV."""
    resp = requests.put(
        f"{CF_API_BASE}/storage/kv/namespaces/{namespace_id}/values/sitemap",
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "text/plain",
        },
        data=sitemap_xml.encode("utf-8"),
    )
    return resp.json().get("success", False)


# ── Read from KV ─────────────────────────────────────────────────────────────

def read_page(api_token: str, namespace_id: str, slug: str) -> Optional[str]:
    """Read a single page from KV."""
    key = f"page:{slug}"
    resp = requests.get(
        f"{CF_API_BASE}/storage/kv/namespaces/{namespace_id}/values/{key}",
        headers={"Authorization": f"Bearer {api_token}"},
    )
    if resp.status_code == 200:
        return resp.text
    return None


def read_manifest(api_token: str, namespace_id: str) -> Optional[dict]:
    """Read the manifest from KV."""
    resp = requests.get(
        f"{CF_API_BASE}/storage/kv/namespaces/{namespace_id}/values/manifest",
        headers={"Authorization": f"Bearer {api_token}"},
    )
    if resp.status_code == 200:
        return resp.json()
    return None


def list_pages(api_token: str, namespace_id: str) -> list:
    """List all page keys in KV."""
    resp = requests.get(
        f"{CF_API_BASE}/storage/kv/namespaces/{namespace_id}/keys",
        headers=_headers(api_token),
        params={"prefix": "page:"},
    )
    data = resp.json()
    return [k["name"].replace("page:", "") for k in data.get("result", [])]


def delete_page(api_token: str, namespace_id: str, slug: str) -> bool:
    """Delete a single page from KV."""
    key = f"page:{slug}"
    resp = requests.delete(
        f"{CF_API_BASE}/storage/kv/namespaces/{namespace_id}/values/{key}",
        headers=_headers(api_token),
    )
    return resp.json().get("success", False)
