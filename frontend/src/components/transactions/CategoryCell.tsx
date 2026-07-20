import { useState } from "react"
import { Check, Loader2, Sparkles } from "lucide-react"
import { toast } from "sonner"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import {
  suggestCategory,
  updateTransaction,
} from "@/lib/api"
import {
  CATEGORY_KINDS,
  type Category,
  type SuggestCategoryResult,
  type Transaction,
} from "@/lib/schemas"
import { extractApiError } from "@/lib/errors"
import { formatAmount, formatDate } from "@/lib/format"
import { cn } from "@/lib/utils"

type CategoryCellProps = {
  tx: Transaction
  categories: Category[]
  onAssigned: (tx: Transaction) => void
}

const REMOVE = "remove"

export function CategoryCell({ tx, categories, onAssigned }: CategoryCellProps) {
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [suggestion, setSuggestion] = useState<SuggestCategoryResult | null>(null)
  const [pending, setPending] = useState<number | typeof REMOVE | null>(null)

  const current = categories.find((c) => c.id === tx.category_id)

  const suggestedName =
    suggestion?.category_id != null
      ? categories.find((c) => c.id === suggestion.category_id)?.name
      : null
  const kindLabel =
    CATEGORY_KINDS.find((k) => k.value === tx.kind)?.label ?? tx.kind
  const filtered = categories.filter((c) => c.is_active && c.kind === tx.kind)

  async function loadSuggestion() {
    if (suggestion != null || loading) return
    setLoading(true)
    try {
      const res = await suggestCategory(tx.description ?? "")
      setSuggestion(res)
    } catch {
      setSuggestion({ category_id: null, category_name: null })
    } finally {
      setLoading(false)
    }
  }

  async function applyCategory(categoryId: number | null) {
    setPending(categoryId == null ? REMOVE : categoryId)
    try {
      const updated = await updateTransaction(tx.id, { category_id: categoryId })
      toast.success("Categoría asignada")
      onAssigned(updated)
      setOpen(false)
    } catch (err) {
      toast.error(
        extractApiError(err) ?? "No pudimos asignar la categoría",
      )
    } finally {
      setPending(null)
    }
  }

  function handleOpenChange(next: boolean) {
    setOpen(next)
    if (next && tx.category_id == null && suggestion == null && !loading) {
      void loadSuggestion()
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {current ? (
          <button
            className="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-left text-sm hover:bg-muted"
            data-testid={`tx-category-cell-${tx.id}`}
          >
            {current.name}
          </button>
        ) : (
          <button
            className={cn(
              "inline-flex items-center gap-1 rounded-md border border-dashed border-border px-1.5 py-0.5 text-left text-sm text-muted-foreground hover:bg-muted",
            )}
            data-testid={`tx-category-cell-${tx.id}`}
          >
            <Sparkles className="h-3.5 w-3.5" />
            Sin categoría
          </button>
        )}
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Asignar categoría</DialogTitle>
          <DialogDescription>
            {tx.description || "Sin descripción"} ·{" "}
            {formatAmount(tx.amount)} · {formatDate(tx.date)} · {kindLabel}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {current ? (
            <div className="rounded-lg border bg-secondary/40 px-3 py-2 text-sm">
              <span className="text-muted-foreground">Actual: </span>
              <span className="font-medium">{current.name}</span>
            </div>
          ) : loading ? (
            <div className="flex items-center gap-2 rounded-lg border bg-secondary/40 px-3 py-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              Buscando sugerencia…
            </div>
          ) : suggestion?.category_id != null ? (
            <div className="rounded-lg border bg-secondary/40 px-3 py-3">
              <div className="flex items-center gap-2 text-sm">
                <Sparkles className="h-4 w-4" />
                <span className="text-muted-foreground">Sugerencia:</span>
                <span className="font-medium">
                  {suggestedName ?? "sugerencia"}
                </span>
              </div>
              <Button
                size="sm"
                className="mt-2 w-full"
                onClick={() => applyCategory(suggestion.category_id)}
                disabled={pending === suggestion.category_id}
                data-testid={`tx-category-suggestion-${tx.id}`}
              >
                {pending === suggestion.category_id ? (
                  <Loader2 className="animate-spin" />
                ) : (
                  <Sparkles />
                )}
                Usar sugerencia
              </Button>
            </div>
          ) : (
            <div className="rounded-lg border bg-secondary/40 px-3 py-2 text-sm text-muted-foreground">
              No encontramos una sugerencia para esta descripción.
            </div>
          )}

          <div className="space-y-2">
            <h4 className="text-sm font-medium">
              {current ? "Cambiar a" : "Elegir categoría"}
            </h4>
            <div className="max-h-72 overflow-y-auto rounded-lg border">
              {filtered.length === 0 ? (
                <div className="px-3 py-4 text-sm text-muted-foreground">
                  No tenés categorías activas de tipo {kindLabel}.
                </div>
              ) : (
                <ul className="divide-y">
                  {filtered.map((c) => (
                    <li key={c.id}>
                      <button
                        type="button"
                        onClick={() => applyCategory(c.id)}
                        disabled={pending !== null}
                        data-testid={`tx-category-option-${c.id}`}
                        className={cn(
                          "flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-muted disabled:opacity-50",
                        )}
                      >
                        <span className="font-medium">{c.name}</span>
                        {c.id === tx.category_id ? (
                          <Check className="h-4 w-4" />
                        ) : pending === c.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : null}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          {current ? (
            <Button
              variant="outline"
              size="sm"
              className="w-full"
              onClick={() => applyCategory(null)}
              disabled={pending !== null}
            >
              {pending === REMOVE ? (
                <Loader2 className="animate-spin" />
              ) : null}
              Quitar categoría
            </Button>
          ) : null}
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => setOpen(false)}
            disabled={pending !== null}
          >
            Cancelar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}