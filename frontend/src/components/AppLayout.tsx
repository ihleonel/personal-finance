import { LogOut } from "lucide-react"
import { Outlet, useNavigate } from "react-router-dom"
import { toast } from "sonner"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/auth/useAuth"

export function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    toast.success("Sesión cerrada")
    navigate("/login", { replace: true })
  }

  return (
    <div className="flex min-h-svh">
      <aside className="hidden w-64 shrink-0 flex-col justify-between border-r bg-card p-6 md:flex">
        <div className="flex flex-col gap-6">
          <div className="flex items-center gap-2 text-lg font-medium">
            <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
              ₪
            </span>
            Personal Finance
          </div>
        </div>
        <div className="flex flex-col gap-3">
          {user?.email ? (
            <p
              className="truncate text-xs text-muted-foreground"
              title={user.email}
            >
              {user.email}
            </p>
          ) : null}
          <Button
            variant="outline"
            className="w-full justify-start"
            onClick={handleLogout}
          >
            <LogOut />
            Cerrar sesión
          </Button>
        </div>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b bg-card px-6 py-4 md:hidden">
          <div className="flex items-center gap-2 text-lg font-medium">
            <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
              ₪
            </span>
            Personal Finance
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleLogout}
            aria-label="Cerrar sesión"
          >
            <LogOut />
          </Button>
        </header>
        <main className="flex-1 p-6 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}