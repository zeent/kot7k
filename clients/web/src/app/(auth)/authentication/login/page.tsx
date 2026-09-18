"use client"

import { useCallback, useEffect, useState }
  from "react"

import { useRouter }
  from "next/navigation"

import { getApiUrl }
  from "@/lib/api/client"

import LoginForm
  from "@/domains/authentication/components/LoginForm"

import { useAuth }
  from "@/domains/authentication/context/AuthContext"

import type { LoginResponse }
  from "@/domains/authentication/types/authentication"

import {
  discoverIdentityProviders,
  type PublicIdentityProvider,
} from "@/domains/authentication/services/providers"


const OIDC_RETURN_TO_KEY = "kot7k.oidc.returnTo"


function safeOidcReturnTo(value: string | null): string | null {
  if (!value) return null

  try {
    const apiOrigin = new URL(getApiUrl("/")).origin
    const target = new URL(value, apiOrigin)
    return target.origin === apiOrigin && target.pathname === "/oauth/authorize/"
      ? target.toString()
      : null
  } catch {
    return null
  }
}


export default function LoginPage() {
  const router =
    useRouter()
  const [externalLoginError, setExternalLoginError] = useState<string | null>(null)
  const [providerError, setProviderError] = useState<string | null>(null)
  const [providers, setProviders] = useState<PublicIdentityProvider[] | null>(null)

  const {
    isAuthenticated,
    isLoading,
    setSession,
  } = useAuth()


  useEffect(() => {
    const returnTo = safeOidcReturnTo(
      new URLSearchParams(window.location.search).get("next"),
    )
    if (returnTo) window.sessionStorage.setItem(OIDC_RETURN_TO_KEY, returnTo)
  }, [])


  const oidcReturnTo = useCallback((): string | null => {
    const queryValue = safeOidcReturnTo(
      new URLSearchParams(window.location.search).get("next"),
    )
    if (queryValue) {
      window.sessionStorage.setItem(OIDC_RETURN_TO_KEY, queryValue)
      return queryValue
    }
    return safeOidcReturnTo(window.sessionStorage.getItem(OIDC_RETURN_TO_KEY))
  }, [])


  const continueAfterLogin = useCallback((): void => {
    const returnTo = oidcReturnTo()
    if (returnTo) {
      window.sessionStorage.removeItem(OIDC_RETURN_TO_KEY)
      window.location.assign(returnTo)
      return
    }
    router.replace("/")
  }, [oidcReturnTo, router])


  useEffect(() => {
    let cancelled = false
    void discoverIdentityProviders().then((result) => {
      if (!cancelled) setProviders(result)
    }).catch(() => {
      if (!cancelled) setProviderError("No s’ha pogut connectar amb el servei d’autenticació. Torna-ho a provar o contacta amb l’administrador.")
    })
    return () => { cancelled = true }
  }, [])


  useEffect(() => {
    if (
      !isLoading
      && isAuthenticated
    ) {
      continueAfterLogin()
    }
  }, [
    isAuthenticated,
    isLoading,
    router,
    continueAfterLogin,
  ])


  useEffect(() => {
    const code = new URLSearchParams(window.location.search).get("code")
    if (!code || isLoading || isAuthenticated) {
      return
    }

    let cancelled = false
    void completeExternalLogin(code)
      .then((response) => {
        if (cancelled) return
        setSession(response)
      })
      .catch((error: unknown) => {
        if (cancelled) return
        setExternalLoginError(
          error instanceof Error
            ? error.message
            : "No s'ha pogut completar l'accés extern.",
        )
        router.replace("/authentication/login")
      })

    return () => {
      cancelled = true
    }
  }, [isAuthenticated, isLoading, router, setSession])


  function handleAuthenticated(
    response: LoginResponse,
  ): void {
    setSession(response)
  }


  if (providerError) {
    return <main><p role="alert">{providerError}</p><button onClick={() => window.location.reload()}>Torna-ho a provar</button></main>
  }

  if (isLoading || !providers) {
    return <main><p role="status">Carregant l’accés…</p></main>
  }


  return (
    <main className="login-page">
      <section
        className="login-page__form"
      >
        <div
          className={
            "login-page__form-inner"
          }
        >
          <LoginForm
            providers={providers}
            onAuthenticated={
              handleAuthenticated
            }
          />
          {externalLoginError && (
            <p role="alert">{externalLoginError}</p>
          )}
        </div>
      </section>


      <section
        className="login-page__visual"
        aria-hidden="true"
      />


      <style jsx>{`
          .login-page {
              display: grid;

              grid-template-columns:
            minmax(28rem, 38%)
            1fr;

              width: 100%;
              min-height: 100vh;

              background: #ffffff;
          }

          .login-page__form {
              display: flex;
              justify-content: center;
              min-width: 0;
              padding: 3rem;
              background: #ffffff;
          }

          .login-page__form-inner {
              width: 100%;
              max-width: 30rem;
          }

          .login-page__visual {
              min-width: 0;
              min-height: 100vh;

              background-image: url("/images/abstract/kot7k-login-blue.png");

              background-position: right center;

              background-repeat: no-repeat;

              background-size: cover;

              -webkit-mask-image:
                linear-gradient(
                  to right,
                  transparent 0,
                  rgba(0, 0, 0, 0.35) 10%,
                  #000000 28%
                );

              mask-image:
                linear-gradient(
                  to right,
                  transparent 0,
                  rgba(0, 0, 0, 0.35) 10%,
                  #000000 28%
                );
          }

          @media (
          max-width: 48rem
          ) {
              .login-page {
                  display: block;
              }

              .login-page__form {
                display: flex;
                align-items: flex-start;
                justify-content: center;
                min-width: 0;
                padding: 1.5rem 3rem 3rem;
                background: #ffffff;
              }

              .login-page__visual {
                  display: none;
              }
          }
      `}</style>
    </main>
  )
}
import { completeExternalLogin }
  from "@/domains/authentication/services/authentication"
