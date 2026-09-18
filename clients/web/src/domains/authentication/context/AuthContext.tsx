"use client"

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react"

import {
  getCurrentUser,
  login,
  logout,
  refreshAccessToken,
} from "@/domains/authentication/services/authentication"

import type {
  AuthUser,
  LoginCredentials,
  LoginResponse,
} from "@/domains/authentication/types/authentication"


type AuthContextValue = {
  user: AuthUser | null
  accessToken: string | null

  isAuthenticated: boolean
  isLoading: boolean

  signIn: (
    credentials: LoginCredentials,
  ) => Promise<void>

  signOut: () => Promise<void>

  refresh: () => Promise<string | null>

  setSession: (
    session: LoginResponse,
  ) => void
}


type AuthProviderProps = {
  children: ReactNode
}


const AuthContext =
  createContext<AuthContextValue | null>(
    null,
  )


export function AuthProvider({
  children,
}: AuthProviderProps) {
  const [
    user,
    setUser,
  ] = useState<AuthUser | null>(
    null,
  )

  const [
    accessToken,
    setAccessToken,
  ] = useState<string | null>(
    null,
  )

  const [
    refreshToken,
    setRefreshToken,
  ] = useState<string | null>(
    null,
  )

  const [
    isLoading,
    setIsLoading,
  ] = useState(true)


  const isAuthenticated =
    user !== null
    && accessToken !== null


  const clearSession =
    useCallback(() => {
      setUser(
        null,
      )

      setAccessToken(
        null,
      )

      setRefreshToken(
        null,
      )

      if (
        typeof window
        !== "undefined"
      ) {
        localStorage.removeItem(
          "accessToken",
        )

        localStorage.removeItem(
          "refreshToken",
        )
      }
    }, [])


  useEffect(() => {
    const onLogout = (event: StorageEvent) => {
      if (event.storageArea === localStorage && (
        event.key === "kot7k.logout"
        || (event.key === "refreshToken" && event.newValue === null)
        || event.key === null
      )) {
        // Reload cancels in-flight restoration requests and clears React state.
        window.location.replace("/authentication/login")
      }
    }
    window.addEventListener("storage", onLogout)
    return () => window.removeEventListener("storage", onLogout)
  }, [])

  const setSession =
    useCallback(
      (
        session: LoginResponse,
      ): void => {
        setUser(
          session.user,
        )

        setAccessToken(
          session.access,
        )

        setRefreshToken(
          session.refresh,
        )

        if (
          typeof window
          !== "undefined"
        ) {
          localStorage.setItem(
            "accessToken",
            session.access,
          )

          localStorage.setItem(
            "refreshToken",
            session.refresh,
          )
        }
      },
      [],
    )


  const refresh =
    useCallback(
      async (): Promise<
        string | null
      > => {
        const currentRefreshToken =
          refreshToken
          ?? (
            typeof window
            !== "undefined"
              ? localStorage.getItem(
                  "refreshToken",
                )
              : null
          )

        if (
          !currentRefreshToken
        ) {
          clearSession()

          return null
        }

        try {
          const response =
            await refreshAccessToken(
              currentRefreshToken,
            )

          setAccessToken(
            response.access,
          )

          if (
            typeof window
            !== "undefined"
          ) {
            localStorage.setItem(
              "accessToken",
              response.access,
            )
          }

          return response.access
        } catch {
          clearSession()

          return null
        }
      },
      [
        clearSession,
        refreshToken,
      ],
    )


  const signIn =
    useCallback(
      async (
        credentials:
          LoginCredentials,
      ): Promise<void> => {
        const response =
          await login(
            credentials,
          )

        setSession(
          response,
        )
      },
      [
        setSession,
      ],
    )


  const signOut =
    useCallback(
      async (): Promise<void> => {
        const currentRefreshToken =
          refreshToken
          ?? (
            typeof window
            !== "undefined"
              ? localStorage.getItem(
                  "refreshToken",
                )
              : null
          )

        try {
          if (
            currentRefreshToken
          ) {
            await logout(
              currentRefreshToken,
            )
          }
        } finally {
          clearSession()
        }
      },
      [
        clearSession,
        refreshToken,
      ],
    )


  useEffect(() => {
    const controller =
      new AbortController()

    async function restoreSession():
      Promise<void> {
      try {
        const storedAccessToken =
          localStorage.getItem(
            "accessToken",
          )

        const storedRefreshToken =
          localStorage.getItem(
            "refreshToken",
          )

        if (
          !storedRefreshToken
        ) {
          clearSession()

          return
        }

        setRefreshToken(
          storedRefreshToken,
        )

        if (
          storedAccessToken
        ) {
          try {
            const currentUser =
              await getCurrentUser(
                storedAccessToken,
                controller.signal,
              )

            if (
              controller.signal.aborted
            ) {
              return
            }

            setAccessToken(
              storedAccessToken,
            )

            setUser(
              currentUser,
            )

            return
          } catch (
            caughtError
          ) {
            if (
              caughtError
                instanceof DOMException
              && caughtError.name
                === "AbortError"
            ) {
              return
            }
          }
        }

        const refreshResponse =
          await refreshAccessToken(
            storedRefreshToken,
            controller.signal,
          )

        if (
          controller.signal.aborted
        ) {
          return
        }

        const access =
          refreshResponse.access

        setAccessToken(
          access,
        )

        localStorage.setItem(
          "accessToken",
          access,
        )

        const currentUser =
          await getCurrentUser(
            access,
            controller.signal,
          )

        if (
          controller.signal.aborted
        ) {
          return
        }

        setUser(
          currentUser,
        )
      } catch (
        caughtError
      ) {
        if (
          caughtError
            instanceof DOMException
          && caughtError.name
            === "AbortError"
        ) {
          return
        }

        clearSession()
      } finally {
        if (
          !controller.signal.aborted
        ) {
          setIsLoading(
            false,
          )
        }
      }
    }

    void restoreSession()

    return () => {
      controller.abort()
    }
  }, [
    clearSession,
  ])


  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,

        isAuthenticated,
        isLoading,

        signIn,
        signOut,
        refresh,
        setSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}


export function useAuth():
  AuthContextValue {
  const context =
    useContext(
      AuthContext,
    )

  if (
    !context
  ) {
    throw new Error(
      "useAuth s'ha d'utilitzar "
      + "dins d'un AuthProvider.",
    )
  }

  return context
}