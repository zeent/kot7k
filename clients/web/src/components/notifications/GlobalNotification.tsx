"use client"

import {
  InlineNotification,
} from "@carbon/react"

import { useNotification }
  from "@/components/notifications/useNotification"


export default function GlobalNotification() {
  const {
    notification,
    clearNotification,
  } = useNotification()

  if (!notification) {
    return null
  }

  return (
    <InlineNotification
      kind={notification.kind}
      lowContrast
      title={notification.title}
      subtitle={notification.subtitle}
      onClose={clearNotification}
      style={{
        width: "100%",
        maxWidth: "none",
        margin: 0,
      }}
    />
  )
}