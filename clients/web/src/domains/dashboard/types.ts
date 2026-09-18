export type DashboardMetric = {
  users: number
  applications: number
  identity_providers: number
}

export type DashboardApplication = {
  id: number
  key: string
  name: string
  description: string
  homepage_url: string
  roles: { key: string; name: string }[]
}

export type AccountActivity = {
  id: number
  action: "login" | "logout" | "role_assigned" | "role_removed"
  description: string
  metadata: Record<string, unknown>
  ip_address: string | null
  created_at: string
}

export type DashboardData = {
  metrics: DashboardMetric
  applications: DashboardApplication[]
  activities: AccountActivity[]
}
