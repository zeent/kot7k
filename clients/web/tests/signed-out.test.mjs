import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import vm from 'node:vm'
const code = readFileSync(new URL('../public/auth/signed-out.js', import.meta.url), 'utf8')
async function run({ matches = true, valid = true, changed = false } = {}) {
  const values = new Map([['accessToken', 'access'], ['refreshToken', 'refresh']])
  const status = { textContent: '' }
  let redirect
  const storage = { getItem: key => values.get(key) ?? null, removeItem: key => values.delete(key), setItem: (key, value) => values.set(key, value) }
  await vm.runInNewContext(code, {
    document: { getElementById: () => status, currentScript: { dataset: { apiOrigin: 'http://localhost:10001' } } },
    localStorage: storage, sessionStorage: { removeItem() {} }, URL, Date, AbortSignal,
    location: { href: 'http://localhost:10000/authentication/signed-out?ticket=signed-ticket', replace: value => { redirect = value } },
    fetch: async (url, options) => {
      assert.equal(url, 'http://localhost:10001/api/authentication/logout/complete/')
      assert.deepEqual(JSON.parse(options.body), { ticket: 'signed-ticket', refresh: 'refresh' })
      if (changed) values.set('refreshToken', 'new-refresh')
      return { ok: valid, json: async () => ({ clear_session: matches, redirect_uri: 'https://registered.example/signed-out' }) }
    },
  })
  return { values, status, redirect }
}
test('signed confirmation clears matching session and returns to registered app', async () => {
  const r = await run(); assert.equal(r.values.get('refreshToken'), undefined); assert.equal(r.redirect, 'https://registered.example/signed-out')
})
test('confirmation for another session preserves current login', async () => {
  const r = await run({ matches: false }); assert.equal(r.values.get('refreshToken'), 'refresh')
})
test('new login during confirmation is preserved', async () => {
  const r = await run({ changed: true }); assert.equal(r.values.get('refreshToken'), 'new-refresh')
})
test('invalid confirmation cannot redirect or clear session', async () => {
  const r = await run({ valid: false }); assert.equal(r.values.get('refreshToken'), 'refresh'); assert.equal(r.redirect, undefined); assert.match(r.status.textContent, /No s’ha pogut/)
})
