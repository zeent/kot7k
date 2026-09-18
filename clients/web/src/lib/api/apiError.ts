export async function getApiErrorMessage(
  response: Response,
  fallbackMessage: string,
): Promise<string> {
  try {
    const data: unknown = await response.json()

    if (
      typeof data !== "object" ||
      data === null
    ) {
      return fallbackMessage
    }

    if (
      "detail" in data &&
      typeof data.detail === "string"
    ) {
      return data.detail
    }

    const messages = Object.entries(data)
      .flatMap(([field, value]) => {
        if (Array.isArray(value)) {
          return value.map(
            (message) =>
              `${field}: ${String(message)}`,
          )
        }

        if (typeof value === "string") {
          return [`${field}: ${value}`]
        }

        if (
          typeof value === "object" &&
          value !== null
        ) {
          return Object.entries(value)
            .flatMap(
              ([nestedField, nestedValue]) => {
                if (Array.isArray(nestedValue)) {
                  return nestedValue.map(
                    (message) =>
                      `${field}.${nestedField}: ${String(message)}`,
                  )
                }

                if (
                  typeof nestedValue === "string"
                ) {
                  return [
                    `${field}.${nestedField}: ${nestedValue}`,
                  ]
                }

                return []
              },
            )
        }

        return []
      })

    return messages.length > 0
      ? messages.join(" ")
      : fallbackMessage
  } catch {
    return fallbackMessage
  }
}