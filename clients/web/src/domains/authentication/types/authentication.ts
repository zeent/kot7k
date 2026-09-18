export type LoginCredentials = {
  email: string
  password: string
}

export type AuthUser = {
  id: number
  first_name: string
  last_name: string
  full_name: string
  email: string
  is_staff: boolean
  is_superuser: boolean
}

export type LoginResponse = {
  user: AuthUser
  access: string
  refresh: string
}

export type RefreshResponse = {
  access: string
}
