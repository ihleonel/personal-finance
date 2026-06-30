import { useEffect, useState } from "react"
import { Loader2, Pencil, Plus, Power, Wallet } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AccountFormDialog } from "@/components/accounts/AccountFormDialog"
import {
  ACCOUNT_TYPES,
  type Account,
} from "@/lib/schemas"
import { deactivateAccount, fetchAccounts } from "@/lib/api"
import { formatBalance } from "@/lib/format"

export function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<Account | null>(null)
  const [confirmingId, setConfirmingId] = useState<number | null>(null)

  useEffect(() => {
    let active = true
    fetchAccounts()
      .then((data) => {
        if (active) {
          setAccounts(data)
          setError(null)
          setLoading(false)
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(
            err instanceof Error ? err.message : "No pudimos cargar tus cuentas",
          )
          setLoading(false)
        }
      })
    return () => {
      active = false
    }
  }, [])

  function handleNew() {
    setEditing(null)
    setDialogOpen(true)
  }

  function handleEdit(account: Account) {
    setEditing(account)
    setDialogOpen(true)
  }

  async function handleDeactivate(id: number) {
    try {
      const updated = await deactivateAccount(id)
      setAccounts((prev) =>
        prev.map((a) => (a.id === updated.id ? updated : a)),
      )
      toast.success("Cuenta desactivada")
    } catch (err) {
      toast.error(
        err instanceof Error
          ? err.message
          : "No pudimos desactivar la cuenta",
      )
    } finally {
      setConfirmingId(null)
    }
  }

  function handleSaved(saved: Account) {
    setAccounts((prev) => {
      const idx = prev.findIndex((a) => a.id === saved.id)
      if (idx === -1) return [saved, ...prev]
      const next = [...prev]
      next[idx] = saved
      return next
    })
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Cuentas</h1>
          <p className="text-muted-foreground">
            Gestioná tus cuentas en distintas monedas.
          </p>
        </div>
        <Button onClick={handleNew}>
          <Plus />
          Nueva cuenta
        </Button>
      </div>

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Tus cuentas</CardTitle>
          <CardDescription>
            Acá aparecen todas las cuentas que creaste, activas e inactivas.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-10 text-muted-foreground">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Cargando…
            </div>
          ) : accounts.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-3 py-10 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                <Wallet className="h-6 w-6 text-muted-foreground" />
              </div>
              <div>
                <p className="font-medium">No tenés cuentas todavía</p>
                <p className="text-sm text-muted-foreground">
                  Creá tu primera cuenta para empezar a gestionar tus finanzas.
                </p>
              </div>
              <Button onClick={handleNew}>
                <Plus />
                Crear cuenta
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nombre</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Moneda</TableHead>
                  <TableHead className="text-right">Saldo inicial</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {accounts.map((account) => {
                  const typeLabel = ACCOUNT_TYPES.find(
                    (t) => t.value === account.account_type,
                  )?.label ?? account.account_type
                  const isConfirming = confirmingId === account.id
                  return (
                    <TableRow key={account.id}>
                      <TableCell className="font-medium">
                        {account.name}
                      </TableCell>
                      <TableCell>{typeLabel}</TableCell>
                      <TableCell>{account.currency}</TableCell>
                      <TableCell className="text-right tabular-nums">
                        {formatBalance(account.initial_balance, account.currency)}
                      </TableCell>
                      <TableCell>
                        <span
                          className={
                            account.is_active
                              ? "inline-flex items-center rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium text-secondary-foreground"
                              : "inline-flex items-center rounded-full bg-destructive/10 px-2.5 py-0.5 text-xs font-medium text-destructive"
                          }
                        >
                          {account.is_active ? "Activo" : "Inactivo"}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        {isConfirming ? (
                          <div className="flex items-center justify-end gap-1">
                            <span className="mr-1 text-xs text-muted-foreground">
                              ¿Seguro?
                            </span>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setConfirmingId(null)}
                              disabled={!account.is_active}
                            >
                              No
                            </Button>
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => handleDeactivate(account.id)}
                              disabled={!account.is_active}
                            >
                              Sí
                            </Button>
                          </div>
                        ) : (
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              onClick={() => handleEdit(account)}
                              aria-label={`Editar ${account.name}`}
                              disabled={!account.is_active}
                            >
                              <Pencil />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              onClick={() => setConfirmingId(account.id)}
                              aria-label={`Desactivar ${account.name}`}
                              disabled={!account.is_active}
                            >
                              <Power />
                            </Button>
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <AccountFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        account={editing}
        onSaved={handleSaved}
      />
    </div>
  )
}