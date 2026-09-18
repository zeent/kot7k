/* Microsoft loads this endpoint in an iframe: never redirect its parent. */
;(async function () {
  const status = document.getElementById("status")
  const apiOrigin = document.currentScript.dataset.apiOrigin
  let refresh
  try { refresh = localStorage.getItem("refreshToken") } catch {
    status.textContent = "El navegador ha bloquejat l’accés a la sessió. Obre KOT7K i tanca la sessió directament."
    return
  }
  if (!refresh) { status.textContent = "No hi ha cap sessió activa."; return }
  try {
    const response = await fetch(`${apiOrigin}/api/authentication/microsoft/logout/`, {
      method: "POST", credentials: "include",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ refresh }), signal: AbortSignal.timeout(10000),
    })
    if (!response.ok) throw new Error("Session revocation failed")
    if (response.status !== 204) {
      status.textContent = "La sessió independent de Microsoft continua oberta."
      return
    }
    // Do not clear a different login completed while the request was in flight.
    if (localStorage.getItem("refreshToken") === refresh) {
      localStorage.removeItem("accessToken")
      localStorage.removeItem("refreshToken")
      localStorage.setItem("kot7k.logout", String(Date.now()))
      sessionStorage.removeItem("kot7k.oidc.returnTo")
    }
    status.textContent = "Sessió de KOT7K tancada."
  } catch {
    status.textContent = "No s’ha pogut confirmar la revocació al servidor. Obre KOT7K i tanca la sessió directament."
  }
})()
