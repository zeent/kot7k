import { apiFetch } from "@/lib/api/client"
import type { DashboardData } from "./types"

export const getDashboard = () => apiFetch<DashboardData>("/dashboard/")
