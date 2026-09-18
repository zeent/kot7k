import {
  getApiErrorMessage,
} from "@/lib/api/apiError"


const CONFIGURED_API_BASE_URL =
  process.env
    .NEXT_PUBLIC_API_BASE_URL
    ?.replace(/\/$/, "")
  ?? "http://localhost:10001"


function getApiBaseUrl(): string {
  const apiUrl = new URL(CONFIGURED_API_BASE_URL)

  if (
    typeof window !== "undefined"
    && window.location.hostname.endsWith(".localhost")
  ) {
    apiUrl.hostname = window.location.hostname
  }

  return `${apiUrl.toString().replace(/\/$/, "")}/api`
}

function normalizeApiPath(
  path: string,
): string {
  return path.startsWith(
    "/",
  )
    ? path
    : `/${path}`
}


function getAccessToken(): string | null {
  if (
    typeof window
    === "undefined"
  ) {
    return null
  }

  return localStorage.getItem(
    "accessToken",
  )
}


function getRefreshToken(): string | null {
  if (
    typeof window
    === "undefined"
  ) {
    return null
  }

  return localStorage.getItem(
    "refreshToken",
  )
}


function setAccessToken(
  accessToken: string,
): void {
  if (
    typeof window
    === "undefined"
  ) {
    return
  }

  localStorage.setItem(
    "accessToken",
    accessToken,
  )
}


function clearTokens(): void {
  if (
    typeof window
    === "undefined"
  ) {
    return
  }

  localStorage.removeItem(
    "accessToken",
  )

  localStorage.removeItem(
    "refreshToken",
  )
}


function isFormDataBody(
  body: BodyInit | null | undefined,
): body is FormData {
  return (
    typeof FormData
    !== "undefined"
    && body instanceof FormData
  )
}


function buildHeaders(
  options?: RequestInit,
  accessToken?: string | null,
): Headers {
  const headers =
    new Headers(
      options?.headers,
    )

  if (
    !headers.has(
      "Accept",
    )
  ) {
    headers.set(
      "Accept",
      "application/json",
    )
  }

  if (
    options?.body
    && !isFormDataBody(
      options.body,
    )
    && !headers.has(
      "Content-Type",
    )
  ) {
    headers.set(
      "Content-Type",
      "application/json",
    )
  }

  if (
    accessToken
    && !headers.has(
      "Authorization",
    )
  ) {
    headers.set(
      "Authorization",
      `Bearer ${accessToken}`,
    )
  }

  return headers
}


type RefreshTokenResponse = {
  access: string
}


async function requestNewAccessToken(): Promise<string | null> {
  const refreshToken =
    getRefreshToken()

  if (
    !refreshToken
  ) {
    return null
  }

  const response =
    await fetch(
      `${getApiBaseUrl()}/authentication/refresh/`,
      {
        method:
          "POST",

        headers: {
          Accept:
            "application/json",

          "Content-Type":
            "application/json",
        },

        body: JSON.stringify({
          refresh:
            refreshToken,
        }),
      },
    )

  if (
    !response.ok
  ) {
    clearTokens()

    return null
  }

  const data =
    await response.json() as RefreshTokenResponse

  setAccessToken(
    data.access,
  )

  return data.access
}


async function performRequest(
  path: string,
  options?: RequestInit,
  accessToken?: string | null,
): Promise<Response> {
  return fetch(
    `${getApiBaseUrl()}${normalizeApiPath(path)}`,
    {
      ...options,

      headers:
        buildHeaders(
          options,
          accessToken,
        ),
    },
  )
}


export async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const accessToken =
    getAccessToken()

  let response =
    await performRequest(
      path,
      options,
      accessToken,
    )

  const canRefresh =
    response.status
    === 401
    && normalizeApiPath(
      path,
    )
    !== "/authentication/refresh/"
    && normalizeApiPath(
      path,
    )
    !== "/authentication/login/"

  if (
    canRefresh
  ) {
    const newAccessToken =
      await requestNewAccessToken()

    if (
      newAccessToken
    ) {
      response =
        await performRequest(
          path,
          options,
          newAccessToken,
        )
    }
  }

  if (
    !response.ok
  ) {
    throw new Error(
      await getApiErrorMessage(
        response,
        (
          "La petició ha fallat: "
          + `${response.status} `
          + response.statusText
        ),
      ),
    )
  }

  if (
    response.status
    === 204
    || response.headers.get(
      "content-length",
    )
    === "0"
  ) {
    return undefined as T
  }

  return response.json() as Promise<T>
}


export function getApiUrl(
  path: string,
): string {
  return (
    `${getApiBaseUrl()}`
    + normalizeApiPath(
      path,
    )
  )
}
