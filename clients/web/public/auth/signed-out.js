;(async function () {
  const status = document.getElementById("status")
  const apiOrigin = document.currentScript.dataset.apiOrigin
  try {
    const refresh = localStorage.getItem("refreshToken")
    const ticket = new URL(location.href).searchParams.get("ticket")
    const response = await fetch(`${apiOrigin}/api/authentication/logout/complete/`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ticket, refresh }), signal: AbortSignal.timeout(10000),
    })
    if (!response.ok) throw new Error("Invalid logout confirmation")
    const result = await response.json()
    if (result.clear_session && localStorage.getItem("refreshToken") === refresh) {
      localStorage.removeItem("accessToken")
      localStorage.removeItem("refreshToken")
      localStorage.setItem("kot7k.logout", String(Date.now()))
      sessionStorage.removeItem("kot7k.oidc.returnTo")
    }
    location.replace(result.redirect_uri || "/authentication/login")
  } catch {
    status.textContent = "No s’ha pogut confirmar la sortida. Torna a KOT7K per comprovar la sessió."
  }
})()
