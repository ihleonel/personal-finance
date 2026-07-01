import { useEffect, useState } from "react"
import { Loader2, Pencil, Plus, Power, Trash2, WandSparkles } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { CategoryRuleFormDialog } from "@/components/categories/CategoryRuleFormDialog"
import {
  RULE_MATCH_TYPES,
  type CategorizationRule,
  type Category,
} from "@/lib/schemas"
import {
  activateCategorizationRule,
  deactivateCategorizationRule,
  deleteCategorizationRule,
  fetchCategorizationRules,
} from "@/lib/api"

type CategoryRulesDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  category: Category | null
}

export function CategoryRulesDialog({
  open,
  onOpenChange,
  category,
}: CategoryRulesDialogProps) {
  const [rules, setRules] = useState<CategorizationRule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<CategorizationRule | null>(null)
  const [confirmingId, setConfirmingId] = useState<number | null>(null)
  const [confirmingAction, setConfirmingAction] = useState<
    "activate" | "deactivate" | "delete" | null
  >(null)

  function handleOpenChange(next: boolean) {
    if (!next) {
      setRules([])
      setLoading(true)
      setError(null)
      setFormOpen(false)
      setEditing(null)
      setConfirmingId(null)
      setConfirmingAction(null)
    }
    onOpenChange(next)
  }

  useEffect(() => {
    if (!open || !category) return
    let active = true
    fetchCategorizationRules()
      .then((all) => {
        if (!active) return
        const mine = all.filter((r) => r.category_id === category.id)
        setRules(mine)
        setError(null)
        setLoading(false)
      })
      .catch((err: unknown) => {
        if (!active) return
        setError(
          err instanceof Error ? err.message : "No pudimos cargar las reglas",
        )
        setLoading(false)
      })
    return () => {
      active = false
    }
  }, [open, category])

  function handleNew() {
    setEditing(null)
    setFormOpen(true)
  }

  function handleEdit(rule: CategorizationRule) {
    setEditing(rule)
    setFormOpen(true)
  }

  async function handleDeactivate(id: number) {
    try {
      const updated = await deactivateCategorizationRule(id)
      setRules((prev) => prev.map((r) => (r.id === updated.id ? updated : r)))
      toast.success("Regla desactivada")
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "No pudimos desactivar la regla",
      )
    } finally {
      setConfirmingId(null)
      setConfirmingAction(null)
    }
  }

  async function handleActivate(id: number) {
    try {
      const updated = await activateCategorizationRule(id)
      setRules((prev) => prev.map((r) => (r.id === updated.id ? updated : r)))
      toast.success("Regla activada")
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "No pudimos activar la regla",
      )
    } finally {
      setConfirmingId(null)
      setConfirmingAction(null)
    }
  }

  async function handleDelete(id: number) {
    try {
      await deleteCategorizationRule(id)
      setRules((prev) => prev.filter((r) => r.id !== id))
      toast.success("Regla eliminada")
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "No pudimos eliminar la regla",
      )
    } finally {
      setConfirmingId(null)
      setConfirmingAction(null)
    }
  }

  function startConfirm(
    rule: CategorizationRule,
    action: "activate" | "deactivate" | "delete",
  ) {
    setConfirmingId(rule.id)
    setConfirmingAction(action)
  }

  function cancelConfirm() {
    setConfirmingId(null)
    setConfirmingAction(null)
  }

  function handleSaved(saved: CategorizationRule) {
    setRules((prev) => {
      const idx = prev.findIndex((r) => r.id === saved.id)
      if (idx === -1) return [saved, ...prev]
      const next = [...prev]
      next[idx] = saved
      return next
    })
  }

  const matchTypeLabel = (value: string) =>
    RULE_MATCH_TYPES.find((m) => m.value === value)?.label ?? value

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-5xl sm:max-w-5xl">
        <DialogHeader>
          <DialogTitle>
            Reglas de categorización
            {category ? ` · ${category.name}` : ""}
          </DialogTitle>
          <DialogDescription>
            Definí patrones para sugerir esta categoría automáticamente según la
            descripción de tus transacciones. Las reglas se evalúan en orden de
            prioridad (mayor primero); solo las activas generan sugerencias.
          </DialogDescription>
        </DialogHeader>

        {error ? (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}

        <div className="flex items-center justify-end">
          <Button onClick={handleNew} size="sm" disabled={!category}>
            <Plus />
            Nueva regla
          </Button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-10 text-muted-foreground">
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Cargando…
          </div>
        ) : rules.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-3 py-10 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
              <WandSparkles className="h-6 w-6 text-muted-foreground" />
            </div>
            <div>
              <p className="font-medium">No tenés reglas para esta categoría</p>
              <p className="text-sm text-muted-foreground">
                Creá una regla para que las transacciones que matcheen se
                sugieran con {category?.name ?? "esta categoría"}.
              </p>
            </div>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Patrón</TableHead>
                <TableHead>Coincidencia</TableHead>
                <TableHead className="text-right">Prioridad</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rules.map((rule) => {
                const isConfirming = confirmingId === rule.id
                return (
                  <TableRow key={rule.id}>
                    <TableCell className="font-medium">
                      {rule.pattern}
                    </TableCell>
                    <TableCell>{matchTypeLabel(rule.match_type)}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      {rule.priority}
                    </TableCell>
                    <TableCell>
                      <span
                        className={
                          rule.is_active
                            ? "inline-flex items-center rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium text-secondary-foreground"
                            : "inline-flex items-center rounded-full bg-destructive/10 px-2.5 py-0.5 text-xs font-medium text-destructive"
                        }
                      >
                        {rule.is_active ? "Activo" : "Inactivo"}
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
                            onClick={cancelConfirm}
                          >
                            No
                          </Button>
                          <Button
                            variant={
                              confirmingAction === "activate"
                                ? "default"
                                : "destructive"
                            }
                            size="sm"
                            onClick={() => {
                              if (confirmingAction === "activate")
                                handleActivate(rule.id)
                              else if (confirmingAction === "deactivate")
                                handleDeactivate(rule.id)
                              else if (confirmingAction === "delete")
                                handleDelete(rule.id)
                            }}
                          >
                            Sí
                          </Button>
                        </div>
                      ) : (
                        <div className="flex items-center justify-end gap-1">
                          {rule.is_active ? (
                            <>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => handleEdit(rule)}
                                aria-label={`Editar regla ${rule.pattern}`}
                              >
                                <Pencil />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => startConfirm(rule, "deactivate")}
                                aria-label={`Desactivar regla ${rule.pattern}`}
                              >
                                <Power />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => startConfirm(rule, "delete")}
                                aria-label={`Eliminar regla ${rule.pattern}`}
                              >
                                <Trash2 />
                              </Button>
                            </>
                          ) : (
                            <>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => startConfirm(rule, "activate")}
                                aria-label={`Activar regla ${rule.pattern}`}
                              >
                                <Power />
                              </Button>
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => startConfirm(rule, "delete")}
                                aria-label={`Eliminar regla ${rule.pattern}`}
                              >
                                <Trash2 />
                              </Button>
                            </>
                          )}
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        )}

        <CategoryRuleFormDialog
          open={formOpen}
          onOpenChange={setFormOpen}
          category={category}
          rule={editing}
          onSaved={handleSaved}
        />
      </DialogContent>
    </Dialog>
  )
}