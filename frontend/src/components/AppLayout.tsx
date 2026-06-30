import { NavLink, Outlet } from "react-router-dom"
import { LayoutDashboard, Wallet, Tags, ArrowRightLeft } from "lucide-react"
import { UserMenu } from "@/components/UserMenu"
import { cn } from "@/lib/utils"

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/accounts", label: "Cuentas", icon: Wallet, end: false },
  { to: "/categories", label: "Categorías", icon: Tags, end: false },
  { to: "/transactions", label: "Transacciones", icon: ArrowRightLeft, end: false },
]

export function AppLayout() {
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
          <nav className="flex flex-col gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-secondary text-secondary-foreground"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground",
                  )
                }
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
        <UserMenu variant="desktop" />
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b bg-card px-6 py-4 md:hidden">
          <div className="flex items-center gap-2 text-lg font-medium">
            <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
              ₪
            </span>
            Personal Finance
          </div>
          <UserMenu variant="compact" />
        </header>
        <main className="flex-1 p-6 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}