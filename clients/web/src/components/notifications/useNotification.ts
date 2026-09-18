"use client"

import { useContext } from "react"

import { NotificationContext }
  from "@/components/notifications/NotificationProvider"


export function useNotification() {
  const context =
    useContext(NotificationContext)

  if (!context) {
    throw new Error(
      "useNotification ha d'utilitzar-se "
      + "dins NotificationProvider.",
    )
  }

  return context
}