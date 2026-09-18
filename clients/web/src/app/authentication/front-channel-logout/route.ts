export const dynamic = "force-dynamic"

export function GET() {
  const apiOrigin = new URL(process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:10001").origin
  const apiAttribute = apiOrigin.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;")
  return new Response(`<!doctype html><html lang="ca"><head><meta charset="utf-8"><title>KOT7K — Logout</title></head><body><p id="status">Tancant la sessió…</p><script src="/auth/front-channel-logout.js" data-api-origin="${apiAttribute}" defer></script></body></html>`, {
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-store",
      "Referrer-Policy": "no-referrer",
      "Content-Security-Policy": `default-src 'none'; script-src 'self'; connect-src ${apiOrigin}; frame-ancestors 'self' https://login.microsoftonline.com https://login.microsoft.com https://login.windows.net; base-uri 'none'; form-action 'none'`,
    },
  })
}
