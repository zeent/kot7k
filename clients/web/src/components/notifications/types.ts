import type { InlineNotificationProps } from "@carbon/react"


export type NotificationKind =
  NonNullable<InlineNotificationProps["kind"]>


export type AppNotification = {
  kind: NotificationKind
  title: string
  subtitle?: string
  timeout?: number
}
