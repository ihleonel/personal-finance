import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useAuth } from "@/auth/useAuth"

export function DashboardPage() {
  const { user } = useAuth()

  const greetingName = user?.first_name?.trim() || user?.email || "usuario"

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="space-y-1">
        <h1 className="text-3xl font-semibold tracking-tight">Hola, {greetingName}</h1>
        {user?.email && (
          <p className="text-muted-foreground">Sesión iniciada como {user.email}.</p>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Tu panel financiero</CardTitle>
          <CardDescription>
            Próximamente vas a ver acá tu balance, gastos recientes y objetivos.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-muted-foreground">
          Por ahora la cuenta está activa y lista para empezar.
        </CardContent>
      </Card>
    </div>
  )
}