import { Navigate, Outlet, useLocation } from "react-router-dom"
import { useAuth } from "@/auth/useAuth"

export function ProtectedRoute() {
  const { status } = useAuth()
  const location = useLocation()

  if (status === "loading") {
    return (
      <div className="flex min-h-svh items-center justify-center">
        <p className="text-sm text-muted-foreground">Cargando…</p>
      </div>
    )
  }

  if (status === "guest") {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return <Outlet />
}
