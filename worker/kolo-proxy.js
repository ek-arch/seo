/**
 * kolo-proxy Cloudflare Worker
 * Routes:
 *   /crypto-card/*  → serve programmatic SEO pages from KV
 *   /sitemap.xml    → merged Webflow + programmatic sitemap
 *   /hex/*          → proxy to Hex API
 *   /collaborator/* → proxy to Collaborator.pro API
 */

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: CORS_HEADERS });
    }

    // ── Programmatic SEO Pages ──
    if (url.pathname.startsWith('/crypto-card/')) {
      return handlePSEOPage(url, env);
    }

    // ── Sitemap (merged) ──
    if (url.pathname === '/sitemap.xml') {
      return handleSitemap(url, env);
    }

    // ── Hex API proxy ──
    if (url.pathname.startsWith('/hex/')) {
      return proxyHex(request, url);
    }

    // ── Collaborator.pro API proxy ──
    if (url.pathname.startsWith('/collaborator/')) {
      return proxyCollaborator(request, url);
    }

    // Pass through to origin
    return fetch(request);
  },
};

// ── Programmatic SEO Page Handler ──

async function handlePSEOPage(url, env) {
  // Extract slug: /crypto-card/uae → uae, /crypto-card/ru/oae → ru/oae
  let slug = url.pathname.replace('/crypto-card/', '').replace(/\/$/, '');

  if (!slug) {
    // /crypto-card/ index — could serve a directory page later
    slug = '__index__';
  }

  try {
    const html = await env.PSEO_PAGES.get(`page:${slug}`);

    if (html) {
      return new Response(html, {
        status: 200,
        headers: {
          'Content-Type': 'text/html;charset=UTF-8',
          'Cache-Control': 'public, max-age=3600, s-maxage=86400',
          'X-Robots-Tag': 'index, follow',
        },
      });
    }
  } catch (e) {
    // KV not bound yet — fall through
  }

  // Page not found — return 404
  return new Response(
    `<!DOCTYPE html><html><head><title>Page Not Found | Kolo</title></head>
     <body style="font-family:sans-serif;text-align:center;padding:80px">
     <h1>404</h1><p>This page doesn't exist yet.</p>
     <a href="https://kolo.xyz">Go to Kolo →</a></body></html>`,
    { status: 404, headers: { 'Content-Type': 'text/html;charset=UTF-8' } }
  );
}

// ── Sitemap Handler ──

async function handleSitemap(url, env) {
  try {
    // Fetch Webflow sitemap
    const webflowResp = await fetch('https://kolo.xyz/sitemap.xml', {
      headers: { 'User-Agent': 'kolo-proxy' },
    });
    let webflowXml = await webflowResp.text();

    // Get programmatic sitemap fragment from KV
    let pseoFragment = '';
    try {
      pseoFragment = await env.PSEO_PAGES.get('sitemap') || '';
    } catch (e) {
      // KV not bound — just serve Webflow sitemap
    }

    if (pseoFragment) {
      // Inject before closing </urlset>
      webflowXml = webflowXml.replace('</urlset>', pseoFragment + '\n</urlset>');
    }

    return new Response(webflowXml, {
      headers: {
        'Content-Type': 'application/xml;charset=UTF-8',
        'Cache-Control': 'public, max-age=3600',
      },
    });
  } catch (e) {
    return new Response(`<error>${e.message}</error>`, {
      status: 500,
      headers: { 'Content-Type': 'application/xml' },
    });
  }
}

// ── Hex API Proxy ──

async function proxyHex(request, url) {
  const path = url.pathname.replace('/hex/', '');
  const target = `https://app.hex.tech/api/v1/${path}`;

  const resp = await fetch(target, {
    method: request.method,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': request.headers.get('Authorization') || '',
    },
    body: request.method !== 'GET' ? await request.text() : undefined,
  });

  const body = await resp.text();
  return new Response(body, {
    status: resp.status,
    headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
  });
}

// ── Collaborator.pro API Proxy ──

async function proxyCollaborator(request, url) {
  const path = url.pathname.replace('/collaborator/', '');
  const target = `https://api.collaborator.pro/v1/${path}${url.search}`;

  const resp = await fetch(target, {
    method: request.method,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': request.headers.get('Authorization') || '',
    },
    body: request.method !== 'GET' ? await request.text() : undefined,
  });

  const body = await resp.text();
  return new Response(body, {
    status: resp.status,
    headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
  });
}
