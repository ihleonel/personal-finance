import { useState } from "react"
import { Loader2 } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { bulkAssignCategory } from "@/lib/api"
import type { Category, Transaction } from "@/lib/schemas"

type BulkAssignCategoryDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  categories: Category[]
  selectedTxs: Transaction[]
  onDone: () => void
}

export function BulkAssignCategoryDialog({
  open,
  onOpenChange,
  categories,
  selectedTxs,
  onDone,
}: BulkAssignCategoryDialogProps) {
  const [categoryId, setCategoryId] = useState<string>("none")
  const [busy, setBusy] = useState(false)

  const selectedKinds = new Set(selectedTxs.map((t) => t.kind))
  const hasMismatch = selectedKinds.size > 1
  const effectiveKind =
    selectedKinds.size === 1 ? [...selectedKinds][0] : null

  const eligibleCategories =
    effectiveKind != null
      ? categories.filter((c) => c.is_active && c.kind === effectiveKind)
      : categories.filter((c) => c.is_active)

  function handleOpenChange(next: boolean) {
    if (next) setCategoryId("none")
    onOpenChange(next)
  }

  async function handleApply() {
    setBusy(true)
    const catId = categoryId === "none" ? null : Number(categoryId)
    try {
      const res = await bulkAssignCategory({
        transaction_ids: selectedTxs.map((t) => t.id),
        category_id: catId,
      })
      reportResult(res.updated_count, res.skipped_kinds.length)
      onDone()
      onOpenChange(false)
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "No pudimos asignar la categoría",
      )
    } finally {
      setBusy(false)
    }
  }

  function reportResult(updated: number, kinds: number) {
    const parts = [`${updated} actualizadas`]
    if (kinds > 0) parts.push(`${kinds} de otro tipo ignoradas`)
    toast.success(parts.join(" · "))
  }

  const targetCount = selectedTxs.length

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Asignar categoría</DialogTitle>
          <DialogDescription>
            Se aplicará a {selectedTxs.length} transacciones seleccionadas.
          </DialogDescription>
        </DialogHeader>

        {hasMismatch ? (
          <p className="text-sm text-destructive">
            Las transacciones seleccionadas son de tipos mixtos (ingreso y
            egreso). Filtrá por tipo antes de asignar una categoría.
          </p>
        ) : (
          <div className="space-y-2">
            <label className="block text-sm font-medium">Categoría</label>
            <Select value={categoryId} onValueChange={setCategoryId}>
              <SelectTrigger data-testid="bulk-category-select">
                <SelectValue placeholder="Sin categoría" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">Sin categoría</SelectItem>
                {eligibleCategories.map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={busy}
          >
            Cancelar
          </Button>
          <Button
            onClick={handleApply}
            disabled={busy || hasMismatch || targetCount === 0}
            data-testid="bulk-apply-btn"
          >
            {busy ? <Loader2 className="animate-spin" /> : null}
            Aplicar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
