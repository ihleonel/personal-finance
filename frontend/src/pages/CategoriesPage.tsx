import { useEffect, useState } from "react"
import { Loader2, Pencil, Plus, Power, Tags, WandSparkles } from "lucide-react"
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
import { CategoryFormDialog } from "@/components/categories/CategoryFormDialog"
import { CategoryRulesDialog } from "@/components/categories/CategoryRulesDialog"
import {
  CATEGORY_KINDS,
  type Category,
} from "@/lib/schemas"
import { activateCategory, deactivateCategory, fetchCategories } from "@/lib/api"

export function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<Category | null>(null)
  const [confirmingId, setConfirmingId] = useState<number | null>(null)
  const [confirmingAction, setConfirmingAction] = useState<"activate" | "deactivate" | null>(null)
  const [rulesDialogOpen, setRulesDialogOpen] = useState(false)
  const [rulesDialogCategory, setRulesDialogCategory] = useState<Category | null>(null)

  useEffect(() => {
    let active = true
    fetchCategories()
      .then((data) => {
        if (active) {
          setCategories(data)
          setError(null)
          setLoading(false)
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(
            err instanceof Error ? err.message : "No pudimos cargar tus categorías",
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

  function handleEdit(category: Category) {
    setEditing(category)
    setDialogOpen(true)
  }

  function handleRules(category: Category) {
    setRulesDialogCategory(category)
    setRulesDialogOpen(true)
  }

  async function handleDeactivate(id: number) {
    try {
      const updated = await deactivateCategory(id)
      setCategories((prev) =>
        prev.map((c) => (c.id === updated.id ? updated : c)),
      )
      toast.success("Categoría desactivada")
    } catch (err) {
      toast.error(
        err instanceof Error
          ? err.message
          : "No pudimos desactivar la categoría",
      )
    } finally {
      setConfirmingId(null)
      setConfirmingAction(null)
    }
  }

  async function handleActivate(id: number) {
    try {
      const updated = await activateCategory(id)
      setCategories((prev) =>
        prev.map((c) => (c.id === updated.id ? updated : c)),
      )
      toast.success("Categoría activada")
    } catch (err) {
      toast.error(
        err instanceof Error
          ? err.message
          : "No pudimos activar la categoría",
      )
    } finally {
      setConfirmingId(null)
      setConfirmingAction(null)
    }
  }

  function startConfirm(category: Category, action: "activate" | "deactivate") {
    setConfirmingId(category.id)
    setConfirmingAction(action)
  }

  function cancelConfirm() {
    setConfirmingId(null)
    setConfirmingAction(null)
  }

  function handleSaved(saved: Category) {
    setCategories((prev) => {
      const idx = prev.findIndex((c) => c.id === saved.id)
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
          <h1 className="text-3xl font-semibold tracking-tight">Categorías</h1>
          <p className="text-muted-foreground">
            Gestioná las categorías para clasificar tus ingresos y egresos.
          </p>
        </div>
        <Button onClick={handleNew}>
          <Plus />
          Nueva categoría
        </Button>
      </div>

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Tus categorías</CardTitle>
          <CardDescription>
            Acá aparecen todas las categorías que creaste, activas e inactivas.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-10 text-muted-foreground">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Cargando…
            </div>
          ) : categories.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-3 py-10 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                <Tags className="h-6 w-6 text-muted-foreground" />
              </div>
              <div>
                <p className="font-medium">No tenés categorías todavía</p>
                <p className="text-sm text-muted-foreground">
                  Creá tu primera categoría para organizar tus movimientos.
                </p>
              </div>
              <Button onClick={handleNew}>
                <Plus />
                Crear categoría
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nombre</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {categories.map((category) => {
                  const kindLabel = CATEGORY_KINDS.find(
                    (k) => k.value === category.kind,
                  )?.label ?? category.kind
                  const isConfirming = confirmingId === category.id
                  return (
                    <TableRow key={category.id}>
                      <TableCell className="font-medium">
                        {category.name}
                      </TableCell>
                      <TableCell>{kindLabel}</TableCell>
                      <TableCell>
                        <span
                          className={
                            category.is_active
                              ? "inline-flex items-center rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium text-secondary-foreground"
                              : "inline-flex items-center rounded-full bg-destructive/10 px-2.5 py-0.5 text-xs font-medium text-destructive"
                          }
                        >
                          {category.is_active ? "Activo" : "Inactivo"}
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
                              variant={confirmingAction === "activate" ? "default" : "destructive"}
                              size="sm"
                              onClick={() =>
                                confirmingAction === "activate"
                                  ? handleActivate(category.id)
                                  : handleDeactivate(category.id)
                              }
                            >
                              Sí
                            </Button>
                          </div>
                        ) : (
                          <div className="flex items-center justify-end gap-1">
                            <Button
                              variant="ghost"
                              size="icon-sm"
                              onClick={() => handleRules(category)}
                              aria-label={`Reglas de ${category.name}`}
                            >
                              <WandSparkles />
                            </Button>
                            {category.is_active ? (
                              <>
                                <Button
                                  variant="ghost"
                                  size="icon-sm"
                                  onClick={() => handleEdit(category)}
                                  aria-label={`Editar ${category.name}`}
                                >
                                  <Pencil />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="icon-sm"
                                  onClick={() => startConfirm(category, "deactivate")}
                                  aria-label={`Desactivar ${category.name}`}
                                >
                                  <Power />
                                </Button>
                              </>
                            ) : (
                              <Button
                                variant="ghost"
                                size="icon-sm"
                                onClick={() => startConfirm(category, "activate")}
                                aria-label={`Activar ${category.name}`}
                              >
                                <Power />
                              </Button>
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
        </CardContent>
      </Card>

      <CategoryFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        category={editing}
        onSaved={handleSaved}
      />

      <CategoryRulesDialog
        key={rulesDialogCategory?.id ?? "none"}
        open={rulesDialogOpen}
        onOpenChange={setRulesDialogOpen}
        category={rulesDialogCategory}
      />
    </div>
  )
}