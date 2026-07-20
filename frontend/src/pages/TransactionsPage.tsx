import { useEffect, useState } from "react"
import { ChevronLeft, ChevronRight, Loader2, Pencil, Plus, Receipt, Tags, Trash2, Upload, X } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
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
import { ImportTransactionsDialog } from "@/components/transactions/ImportTransactionsDialog"
import { CategoryCell } from "@/components/transactions/CategoryCell"
import { BulkAssignCategoryDialog } from "@/components/transactions/BulkAssignCategoryDialog"
import {
  TRANSACTION_KINDS,
  type Account,
  type Category,
  type Transaction,
  type TransactionFilters,
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
  const [importDialogOpen, setImportDialogOpen] = useState(false)
  const [confirmingId, setConfirmingId] = useState<number | null>(null)
  const [selected, setSelected] = useState<Set<number>>(new Set())
  const [bulkDialogOpen, setBulkDialogOpen] = useState(false)

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
    try {
      await deleteTransaction(id)
      setTransactions((prev) => prev.filter((t) => t.id !== id))
      setCount((prev) => prev - 1)
      setPage((prevPage) => {
        const remaining = transactions.length - 1
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
    setSelected(new Set())
    setFilters((prev) => ({ ...prev, [key]: value || undefined }))
  }

  function clearFilters() {
    setLoading(true)
    setPage(1)
    setSelected(new Set())
    setFilters({})
  }

  const allSelectableSelected =
    transactions.length > 0 &&
    transactions.every((t) => selected.has(t.id))
  const someSelectableSelected =
    transactions.some((t) => selected.has(t.id)) && !allSelectableSelected

  function toggleSelectAll() {
    setSelected((prev) => {
      const next = new Set(prev)
      if (allSelectableSelected) {
        for (const t of transactions) next.delete(t.id)
      } else {
        for (const t of transactions) next.add(t.id)
      }
      return next
    })
  }

  function toggleSelect(id: number) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  function openBulkSelection() {
    setBulkDialogOpen(true)
  }

  async function handleBulkDone() {
    setSelected(new Set())
    setLoading(true)
    try {
      const data = await fetchTransactions(filters, page)
      setTransactions(data.results)
      setCount(data.count)
      setError(null)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "No pudimos cargar tus transacciones",
      )
    } finally {
      setLoading(false)
    }
  }

  const accountName = (id: number) =>
    accounts.find((a) => a.id === id)?.name ?? "—"
  const categoryIsBalanceMovement = (categoryId: number | null) => {
    if (categoryId == null) return false
    const cat = categories.find((c) => c.id === categoryId)
    return cat != null && !cat.include_in_summaries
  }
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
                value={
                  filters.category_id_isnull
                    ? "none"
                    : filters.category_id != null
                      ? String(filters.category_id)
                      : "all"
                }
                onValueChange={(v) => {
                  setLoading(true)
                  setPage(1)
                  setSelected(new Set())
                  if (v === "all") {
                    setFilters((prev) => {
                      const next = { ...prev }
                      delete next.category_id
                      delete next.category_id_isnull
                      return next
                    })
                  } else if (v === "none") {
                    setFilters((prev) => {
                      const next = { ...prev }
                      delete next.category_id
                      return { ...next, category_id_isnull: true }
                    })
                  } else {
                    setFilters((prev) => {
                      const next = { ...prev }
                      delete next.category_id_isnull
                      return { ...next, category_id: Number(v) }
                    })
                  }
                }}
              >
                <SelectTrigger className="w-[160px]" data-testid="filter-category-select">
                  <SelectValue placeholder="Todas" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  <SelectItem value="none">Sin categoría</SelectItem>
                  {categories.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      {c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Descripción</label>
              <Input
                type="text"
                placeholder="Buscar…"
                className="w-[200px]"
                data-testid="filter-description"
                value={filters.description ?? ""}
                onChange={(e) => updateFilter("description", e.target.value)}
              />
            </div>

            <Button variant="ghost" onClick={clearFilters}>
              Limpiar
            </Button>
          </div>
        </CardContent>
      </Card>

      {selected.size > 0 ? (
        <div
          className="sticky bottom-4 z-10 mx-auto flex max-w-5xl items-center gap-3 rounded-lg border bg-background/95 p-3 shadow-lg backdrop-blur supports-[backdrop-filter]:bg-background/60"
          data-testid="bulk-action-bar"
        >
          <span className="text-sm font-medium">
            {selected.size} {selected.size === 1 ? "seleccionada" : "seleccionadas"}
          </span>
          <Button size="sm" onClick={openBulkSelection} data-testid="bulk-assign-selection-btn">
            <Tags />
            Asignar categoría
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setSelected(new Set())}
          >
            <X />
            Limpiar
          </Button>
        </div>
      ) : null}

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Movimientos</CardTitle>
              <CardDescription>
                Acá aparecen todas las transacciones que registraste.
              </CardDescription>
            </div>
          </div>
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
                  <TableHead className="w-10">
                    <Checkbox
                      checked={
                        allSelectableSelected
                          ? true
                          : someSelectableSelected
                            ? "indeterminate"
                            : false
                      }
                      onCheckedChange={toggleSelectAll}
                      aria-label="Seleccionar todas"
                      data-testid="bulk-select-all"
                    />
                  </TableHead>
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
                  const isConfirming = confirmingId === tx.id
                  const isSelected = selected.has(tx.id)
                  const signedAmount = tx.kind === "income" ? `+${formatAmount(tx.amount)}` : `−${formatAmount(tx.amount)}`
                  const amountColor = tx.kind === "income"
                    ? "text-secondary-foreground"
                    : "text-destructive"
                  return (
                    <TableRow key={tx.id} data-selected={isSelected}>
                      <TableCell>
                        <Checkbox
                          checked={isSelected}
                          onCheckedChange={() => toggleSelect(tx.id)}
                          aria-label="Seleccionar transacción"
                          data-testid={`bulk-select-${tx.id}`}
                        />
                      </TableCell>
                      <TableCell className="whitespace-nowrap">
                        {formatDate(tx.date)}
                      </TableCell>
                      <TableCell className="font-medium">
                        {tx.description || "—"}
                      </TableCell>
                      <TableCell>{accountName(tx.account_id)}</TableCell>
                      <TableCell>
                        <CategoryCell
                          tx={tx}
                          categories={categories}
                          onAssigned={handleTxSaved}
                        />
                      </TableCell>
                      <TableCell>
                        {categoryIsBalanceMovement(tx.category_id) ? (
                          <span className="inline-flex items-center rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-medium text-amber-700 dark:text-amber-400">
                            Mov. patrimonial
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
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              onClick={() => handleEditTx(tx)}
                              aria-label="Editar transacción"
                            >
                              <Pencil />
                            </Button>
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
                  onClick={() => { setLoading(true); setSelected(new Set()); setPage((p) => Math.max(1, p - 1)) }}
                  disabled={page <= 1}
                  data-testid="tx-pagination-prev"
                >
                  <ChevronLeft />
                  Anterior
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => { setLoading(true); setSelected(new Set()); setPage((p) => p + 1) }}
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

      <ImportTransactionsDialog
        open={importDialogOpen}
        onOpenChange={setImportDialogOpen}
        accounts={accounts}
        onImported={handleImported}
      />

      <BulkAssignCategoryDialog
        open={bulkDialogOpen}
        onOpenChange={setBulkDialogOpen}
        categories={categories}
        selectedTxs={transactions.filter((t) => selected.has(t.id))}
        onDone={handleBulkDone}
      />
    </div>
  )
}