import { useEffect, useState } from "react"
import { ArrowRightLeft, ChevronLeft, ChevronRight, Loader2, Pencil, Plus, Receipt, Trash2, Upload } from "lucide-react"
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
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { TransactionFormDialog } from "@/components/transactions/TransactionFormDialog"
import { TransferFormDialog } from "@/components/transactions/TransferFormDialog"
import { ImportTransactionsDialog } from "@/components/transactions/ImportTransactionsDialog"
import {
  TRANSACTION_KINDS,
  type Account,
  type Category,
  type Transaction,
  type TransactionFilters,
  type TransferOutput,
} from "@/lib/schemas"

const PAGE_SIZE = 30
import {
  deleteTransaction,
  fetchAccounts,
  fetchCategories,
  fetchTransactions,
} from "@/lib/api"
import { formatAmount, formatDate } from "@/lib/format"

export function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<TransactionFilters>({})
  const [page, setPage] = useState(1)
  const [count, setCount] = useState(0)
  const [txDialogOpen, setTxDialogOpen] = useState(false)
  const [editing, setEditing] = useState<Transaction | null>(null)
  const [transferDialogOpen, setTransferDialogOpen] = useState(false)
  const [importDialogOpen, setImportDialogOpen] = useState(false)
  const [confirmingId, setConfirmingId] = useState<number | null>(null)

  useEffect(() => {
    let active = true
    Promise.all([fetchAccounts(), fetchCategories()])
      .then(([accts, cats]) => {
        if (active) {
          setAccounts(accts)
          setCategories(cats)
        }
      })
      .catch(() => {
        // accounts/categories load failure is non-fatal for listing transactions
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    let active = true
    fetchTransactions(filters, page)
      .then((data) => {
        if (active) {
          setTransactions(data.results)
          setCount(data.count)
          setError(null)
          setLoading(false)
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(
            err instanceof Error ? err.message : "No pudimos cargar tus transacciones",
          )
          setLoading(false)
        }
      })
    return () => {
      active = false
    }
  }, [filters, page])

  function handleNewTx() {
    setEditing(null)
    setTxDialogOpen(true)
  }

  function handleEditTx(tx: Transaction) {
    setEditing(tx)
    setTxDialogOpen(true)
  }

  function handleTxSaved(saved: Transaction) {
    if (page > 1) {
      setLoading(true)
      fetchTransactions(filters, page)
        .then((data) => {
          setTransactions(data.results)
          setCount(data.count)
          setError(null)
        })
        .catch((err: unknown) => {
          setError(
            err instanceof Error ? err.message : "No pudimos cargar tus transacciones",
          )
        })
        .finally(() => setLoading(false))
      return
    }
    setTransactions((prev) => {
      const idx = prev.findIndex((t) => t.id === saved.id)
      if (idx === -1) return [saved, ...prev]
      const next = [...prev]
      next[idx] = saved
      return next
    })
  }

  function handleTransferSaved(transfer: TransferOutput) {
    if (page > 1) {
      setLoading(true)
      fetchTransactions(filters, page)
        .then((data) => {
          setTransactions(data.results)
          setCount(data.count)
          setError(null)
        })
        .catch((err: unknown) => {
          setError(
            err instanceof Error ? err.message : "No pudimos cargar tus transacciones",
          )
        })
        .finally(() => setLoading(false))
      return
    }
    setTransactions((prev) => [transfer.source, transfer.destination, ...prev])
  }

  function handleImported() {
    setLoading(true)
    fetchTransactions(filters, page)
      .then((data) => {
        setTransactions(data.results)
        setCount(data.count)
        setError(null)
      })
      .catch((err: unknown) => {
        setError(
          err instanceof Error ? err.message : "No pudimos cargar tus transacciones",
        )
      })
      .finally(() => setLoading(false))
  }

  async function handleDelete(id: number) {
    const target = transactions.find((t) => t.id === id)
    const groupId = target?.transfer_group_id ?? null
    try {
      await deleteTransaction(id)
      setTransactions((prev) => {
        if (groupId != null) {
          return prev.filter((t) => t.transfer_group_id !== groupId)
        }
        return prev.filter((t) => t.id !== id)
      })
      setCount((prev) => prev - (groupId != null ? 2 : 1))
      setPage((prevPage) => {
        const remaining = transactions.length - (groupId != null ? 2 : 1)
        if (prevPage > 1 && remaining === 0) {
          return prevPage - 1
        }
        return prevPage
      })
      toast.success("Transacción eliminada")
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "No pudimos eliminar la transacción",
      )
    } finally {
      setConfirmingId(null)
    }
  }

  function updateFilter<K extends keyof TransactionFilters>(
    key: K,
    value: TransactionFilters[K],
  ) {
    setLoading(true)
    setPage(1)
    setFilters((prev) => ({ ...prev, [key]: value || undefined }))
  }

  function clearFilters() {
    setLoading(true)
    setPage(1)
    setFilters({})
  }

  const accountName = (id: number) =>
    accounts.find((a) => a.id === id)?.name ?? "—"
  const categoryName = (id: number | null) =>
    id == null ? "—" : categories.find((c) => c.id === id)?.name ?? "—"
  const totalPages = Math.max(1, Math.ceil(count / PAGE_SIZE))

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Transacciones</h1>
          <p className="text-muted-foreground">
            Registrá tus ingresos, egresos y transferencias entre cuentas.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => setTransferDialogOpen(true)}>
            <ArrowRightLeft />
            Nueva transferencia
          </Button>
          <Button variant="outline" onClick={() => setImportDialogOpen(true)}>
            <Upload />
            Importar
          </Button>
          <Button onClick={handleNewTx}>
            <Plus />
            Nueva transacción
          </Button>
        </div>
      </div>

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Filtros</CardTitle>
          <CardDescription>
            Acotá el listado por tipo, cuenta, categoría o rango de fechas.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-3">
            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Tipo</label>
              <Select
                value={filters.kind ?? "all"}
                onValueChange={(v) => updateFilter("kind", v === "all" ? undefined : v)}
              >
                <SelectTrigger className="w-[150px]" data-testid="filter-kind-select">
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  {TRANSACTION_KINDS.map((k) => (
                    <SelectItem key={k.value} value={k.value}>
                      {k.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Cuenta</label>
              <Select
                value={filters.account_id != null ? String(filters.account_id) : "all"}
                onValueChange={(v) =>
                  updateFilter("account_id", v === "all" ? undefined : Number(v))
                }
              >
                <SelectTrigger className="w-[160px]" data-testid="filter-account-select">
                  <SelectValue placeholder="Todas" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  {accounts.map((a) => (
                    <SelectItem key={a.id} value={String(a.id)}>
                      {a.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Categoría</label>
              <Select
                value={filters.category_id != null ? String(filters.category_id) : "all"}
                onValueChange={(v) =>
                  updateFilter("category_id", v === "all" ? undefined : Number(v))
                }
              >
                <SelectTrigger className="w-[160px]" data-testid="filter-category-select">
                  <SelectValue placeholder="Todas" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  {categories.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      {c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Desde</label>
              <Input
                type="date"
                className="w-[160px]"
                data-testid="filter-date-from"
                value={filters.date_from ?? ""}
                onChange={(e) => updateFilter("date_from", e.target.value)}
              />
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Hasta</label>
              <Input
                type="date"
                className="w-[160px]"
                data-testid="filter-date-to"
                value={filters.date_to ?? ""}
                onChange={(e) => updateFilter("date_to", e.target.value)}
              />
            </div>

            <Button variant="ghost" onClick={clearFilters}>
              Limpiar
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Movimientos</CardTitle>
          <CardDescription>
            Acá aparecen todas las transacciones que registraste.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-10 text-muted-foreground">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Cargando…
            </div>
          ) : transactions.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-3 py-10 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                <Receipt className="h-6 w-6 text-muted-foreground" />
              </div>
              <div>
                <p className="font-medium">No tenés transacciones todavía</p>
                <p className="text-sm text-muted-foreground">
                  Registrá tu primer ingreso o egreso para empezar a llevar tu
                  control.
                </p>
              </div>
              <Button onClick={handleNewTx}>
                <Plus />
                Crear transacción
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Fecha</TableHead>
                  <TableHead>Descripción</TableHead>
                  <TableHead>Cuenta</TableHead>
                  <TableHead>Categoría</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead className="text-right">Monto</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {transactions.map((tx) => {
                  const isTransfer = tx.transfer_group_id != null
                  const isConfirming = confirmingId === tx.id
                  const signedAmount = tx.kind === "income" ? `+${formatAmount(tx.amount)}` : `−${formatAmount(tx.amount)}`
                  const amountColor = isTransfer
                    ? "text-foreground"
                    : tx.kind === "income"
                      ? "text-secondary-foreground"
                      : "text-destructive"
                  return (
                    <TableRow key={tx.id}>
                      <TableCell className="whitespace-nowrap">
                        {formatDate(tx.date)}
                      </TableCell>
                      <TableCell className="font-medium">
                        {tx.description || "—"}
                      </TableCell>
                      <TableCell>{accountName(tx.account_id)}</TableCell>
                      <TableCell>{categoryName(tx.category_id)}</TableCell>
                      <TableCell>
                        {isTransfer ? (
                          <span className="inline-flex items-center rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium text-muted-foreground">
                            Transferencia
                          </span>
                        ) : (
                          <span
                            className={
                              tx.kind === "income"
                                ? "inline-flex items-center rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium text-secondary-foreground"
                                : "inline-flex items-center rounded-full bg-destructive/10 px-2.5 py-0.5 text-xs font-medium text-destructive"
                            }
                          >
                            {tx.kind === "income" ? "Ingreso" : "Egreso"}
                          </span>
                        )}
                      </TableCell>
                      <TableCell className={`text-right tabular-nums ${amountColor}`}>
                        {signedAmount}
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
                            >
                              No
                            </Button>
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => handleDelete(tx.id)}
                            >
                              Sí
                            </Button>
                          </div>
                        ) : (
                          <div className="flex items-center justify-end gap-1">
                            {!isTransfer ? (
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => handleEditTx(tx)}
                                aria-label="Editar transacción"
                              >
                                <Pencil />
                              </Button>
                            ) : null}
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              onClick={() => setConfirmingId(tx.id)}
                              aria-label="Eliminar transacción"
                            >
                              <Trash2 />
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

          {count > 0 ? (
            <div className="mt-4 flex items-center justify-between border-t pt-4">
              <p className="text-sm text-muted-foreground" data-testid="tx-pagination-info">
                {count} {count === 1 ? "movimiento" : "movimientos"} · Página {page} de {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => { setLoading(true); setPage((p) => Math.max(1, p - 1)) }}
                  disabled={page <= 1}
                  data-testid="tx-pagination-prev"
                >
                  <ChevronLeft />
                  Anterior
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => { setLoading(true); setPage((p) => p + 1) }}
                  disabled={page >= totalPages}
                  data-testid="tx-pagination-next"
                >
                  Siguiente
                  <ChevronRight />
                </Button>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <TransactionFormDialog
        open={txDialogOpen}
        onOpenChange={setTxDialogOpen}
        transaction={editing}
        accounts={accounts}
        categories={categories}
        onSaved={handleTxSaved}
      />

      <TransferFormDialog
        open={transferDialogOpen}
        onOpenChange={setTransferDialogOpen}
        accounts={accounts}
        categories={categories}
        onSaved={handleTransferSaved}
      />

      <ImportTransactionsDialog
        open={importDialogOpen}
        onOpenChange={setImportDialogOpen}
        accounts={accounts}
        onImported={handleImported}
      />
    </div>
  )
}