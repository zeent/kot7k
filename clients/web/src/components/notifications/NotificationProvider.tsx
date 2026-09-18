"use client"

import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"

import type {
  AppNotification,
} from "@/components/notifications/types"


type NotificationContextValue = {
  notification: AppNotification | null
  notify: (notification: AppNotification) => void
  clearNotification: () => void
}


export const NotificationContext =
  createContext<NotificationContextValue | null>(
    null,
  )


type NotificationProviderProps = {
  children: ReactNode
}


const DEFAULT_TIMEOUT = 5000


export default function NotificationProvider({
  children,
}: NotificationProviderProps) {
  const [
    notification,
    setNotification,
  ] = useState<AppNotification | null>(
    null,
  )


  const clearNotification = useCallback(
    (): void => {
      setNotification(null)
    },
    [],
  )


  const notify = useCallback(
    (
      nextNotification: AppNotification,
    ): void => {
      setNotification(nextNotification)
    },
    [],
  )


  useEffect(() => {
    if (!notification) {
      return
    }

    const timeout =
      notification.timeout
      ?? DEFAULT_TIMEOUT

    if (timeout <= 0) {
      return
    }

    const timeoutId = window.setTimeout(
      () => {
        clearNotification()
      },
      timeout,
    )

    return () => {
      window.clearTimeout(
        timeoutId,
      )
    }
  }, [
    notification,
    clearNotification,
  ])


  const value = useMemo(
    () => ({
      notification,
      notify,
      clearNotification,
    }),
    [
      notification,
      notify,
      clearNotification,
    ],
  )


  return (
    <NotificationContext.Provider
      value={value}
    >
      {children}
    </NotificationContext.Provider>
  )
}