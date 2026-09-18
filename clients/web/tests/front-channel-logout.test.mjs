import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import vm from 'node:vm'
const code = readFileSync(new URL('../public/auth/front-channel-logout.js', import.meta.url), 'utf8')
function storage(entries) {
  const values = new Map(Object.entries(entries))
  return { getItem: key => values.get(key) ?? null, removeItem: key => values.delete(key), setItem: (key, value) => values.set(key, value) }
}
async function run({ token = 'test-refresh', failure = false, blocked = false, local = false } = {}) {
  const localStorage = storage(token ? { accessToken: 'test-access', refreshToken: token } : {})
  const sessionStorage = storage({ 'kot7k.oidc.returnTo': '/old-flow' })
  if (blocked) localStorage.getItem = () => { throw new Error('Blocked') }
  const status = { textContent: '' }
  const calls = []
  await vm.runInNewContext(code, { document: { getElementById: () => status, currentScript: { dataset: { apiOrigin: 'http://localhost:10001' } } }, localStorage, sessionStorage, Date, AbortSignal, fetch: async (...args) => { calls.push(args); return { ok: !failure, status: local ? 200 : 204 } } })
  return { localStorage, sessionStorage, status, calls }
}
test('clears browser session and revokes refresh token', async () => {
  const r = await run()
  assert.equal(r.localStorage.getItem('refreshToken'), null)
  assert.equal(r.localStorage.getItem('accessToken'), null)
  assert.ok(r.localStorage.getItem('kot7k.logout'))
  assert.equal(r.sessionStorage.getItem('kot7k.oidc.returnTo'), null)
  assert.equal(r.calls[0][0], 'http://localhost:10001/api/authentication/microsoft/logout/')
  assert.deepEqual(JSON.parse(r.calls[0][1].body), { refresh: 'test-refresh' })
  assert.equal(r.calls[0][1].credentials, 'include')
})
test('repeated logout without tokens succeeds without API call', async () => {
  const r = await run({ token: null }); assert.equal(r.calls.length, 0); assert.match(r.status.textContent, /cap sessió/)
})
test('revocation failure preserves session and reports failure', async () => {
  const r = await run({ failure: true }); assert.equal(r.localStorage.getItem('refreshToken'), 'test-refresh'); assert.match(r.status.textContent, /No s’ha pogut/)
})
test('blocked iframe storage does not claim success', async () => {
  const r = await run({ blocked: true }); assert.equal(r.calls.length, 0); assert.match(r.status.textContent, /bloquejat/)
})

test('Microsoft logout preserves an independent Django session', async () => {
  const r = await run({ local: true }); assert.equal(r.localStorage.getItem('refreshToken'), 'test-refresh'); assert.match(r.status.textContent, /independent/)
})
