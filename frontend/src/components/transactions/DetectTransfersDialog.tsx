import { useState } from "react"
import { Loader2, Search } from "lucide-react"
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
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  type Account,
  type DetectTransfersInput,
  type TransferPairSuggestion,
  type TransferOutput,
} from "@/lib/schemas"
import { detectTransfers, linkTransfer } from "@/lib/api"
import { extractApiError } from "@/lib/errors"
import { formatAmount, formatDate } from "@/lib/format"

type DetectTransfersDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  accounts: Account[]
  onLinked: (transfer: TransferOutput) => void
}

type PendingPair = TransferPairSuggestion

export function DetectTransfersDialog({
  open,
  onOpenChange,
  accounts,
  onLinked,
}: DetectTransfersDialogProps) {
  const activeAccounts = accounts.filter((a) => a.is_active)
  const [windowDays, setWindowDays] = useState("3")
  const [amountTolerance, setAmountTolerance] = useState("0.00")
  const [accountId, setAccountId] = useState<number | "all">("all")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [detecting, setDetecting] = useState(false)
  const [pairs, setPairs] = useState<PendingPair[]>([])
  const [confirmingId, setConfirmingId] = useState<number | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [hasDetected, setHasDetected] = useState(false)
  const [prevOpen, setPrevOpen] = useState(open)

  if (open !== prevOpen) {
    setPrevOpen(open)
    if (open) {
      setWindowDays("3")
      setAmountTolerance("0.00")
      setAccountId("all")
      setDateFrom("")
      setDateTo("")
      setDetecting(false)
      setPairs([])
      setConfirmingId(null)
      setSubmitError(null)
      setHasDetected(false)
    }
  }

  function handleOpenChange(next: boolean) {
    if (!next) setSubmitError(null)
    onOpenChange(next)
  }

  const accountName = (id: number) =>
    accounts.find((a) => a.id === id)?.name ?? "—"

  async function handleDetect() {
    setSubmitError(null)
    setDetecting(true)
    try {
      const input: DetectTransfersInput = {
        window_days: Number(windowDays) || 3,
        amount_tolerance: amountTolerance || "0.00",
      }
      if (accountId !== "all") input.account_id = Number(accountId)
      if (dateFrom) input.date_from = dateFrom
      if (dateTo) input.date_to = dateTo
      const result = await detectTransfers(input)
      setPairs(result.suggestions)
      setHasDetected(true)
    } catch (err) {
      setSubmitError(extractApiError(err) ?? "No pudimos detectar transferencias")
    } finally {
      setDetecting(false)
    }
  }

  async function handleConfirm(pair: TransferPairSuggestion) {
    setConfirmingId(pair.source_id)
    try {
      const transfer = await linkTransfer({
        source_id: pair.source_id,
        destination_id: pair.destination_id,
      })
      toast.success("Transferencia confirmada")
      setPairs((prev) =>
        prev.filter(
          (p) =>
            p.source_id !== pair.source_id && p.destination_id !== pair.destination_id,
        ),
      )
      onLinked(transfer)
    } catch (err) {
      toast.error(extractApiError(err) ?? "No pudimos confirmar la transferencia")
    } finally {
      setConfirmingId(null)
    }
  }

  function handleDismiss(pair: TransferPairSuggestion) {
    setPairs((prev) =>
      prev.filter(
        (p) =>
          p.source_id !== pair.source_id && p.destination_id !== pair.destination_id,
      ),
    )
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-2xl" data-testid="detect-transfers-dialog">
        <DialogHeader>
          <DialogTitle>Detectar transferencias</DialogTitle>
          <DialogDescription>
            Buscamos pares de egreso e ingreso entre tus cuentas que podrían ser
            transferencias. Confirmalos para dejar de tener ingresos y egresos
            inflados.
          </DialogDescription>
        </DialogHeader>

        {submitError ? (
          <Alert variant="destructive">
            <AlertDescription>{submitError}</AlertDescription>
          </Alert>
        ) : null}

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <div className="space-y-1.5">
            <label className="block text-sm font-medium">Ventana (días)</label>
            <Input
              type="number"
              min={0}
              max={30}
              value={windowDays}
              data-testid="detect-window-days"
              disabled={detecting}
              onChange={(e) => setWindowDays(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <label className="block text-sm font-medium">Tolerancia monto</label>
            <Input
              type="text"
              placeholder="0.00"
              value={amountTolerance}
              data-testid="detect-amount-tolerance"
              disabled={detecting}
              onChange={(e) => setAmountTolerance(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <label className="block text-sm font-medium">Cuenta</label>
            <Select
              value={accountId === "all" ? "all" : String(accountId)}
              onValueChange={(v) => setAccountId(v === "all" ? "all" : Number(v))}
              disabled={detecting}
            >
              <SelectTrigger data-testid="detect-account-select">
                <SelectValue placeholder="Todas" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Todas</SelectItem>
                {activeAccounts.map((a) => (
                  <SelectItem key={a.id} value={String(a.id)}>
                    {a.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <label className="block text-sm font-medium">Desde</label>
            <Input
              type="date"
              value={dateFrom}
              data-testid="detect-date-from"
              disabled={detecting}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <label className="block text-sm font-medium">Hasta</label>
            <Input
              type="date"
              value={dateTo}
              data-testid="detect-date-to"
              disabled={detecting}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
          <div className="flex items-end">
            <Button
              onClick={handleDetect}
              disabled={detecting}
              data-testid="detect-submit"
              className="w-full"
            >
              {detecting ? (
                <>
                  <Loader2 className="animate-spin" />
                  Buscando…
                </>
              ) : (
                <>
                  <Search />
                  Detectar
                </>
              )}
            </Button>
          </div>
        </div>

        {hasDetected ? (
          pairs.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
              No encontramos posibles transferencias con esos criterios.
            </div>
          ) : (
            <div
              className="max-h-80 space-y-2 overflow-y-auto"
              data-testid="detect-transfers-list"
            >
              {pairs.map((pair) => {
                const scorePct = Math.round(pair.score * 100)
                const isConfirming = confirmingId === pair.source_id
                return (
                  <div
                    key={`${pair.source_id}-${pair.destination_id}`}
                    className="rounded-lg border border-amber-500/40 bg-amber-500/5 p-3"
                  >
                    <div className="flex flex-wrap items-center gap-2 text-sm">
                      <span className="font-medium">
                        {accountName(pair.source_account_id)}
                      </span>
                      <span className="text-muted-foreground">→</span>
                      <span className="font-medium">
                        {accountName(pair.destination_account_id)}
                      </span>
                      <span className="ml-auto font-medium tabular-nums">
                        {formatAmount(pair.amount)}
                      </span>
                    </div>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      <span>Egreso: {formatDate(pair.source_date)}</span>
                      <span>·</span>
                      <span>Ingreso: {formatDate(pair.destination_date)}</span>
                      <span>·</span>
                      <span
                        className="rounded-full bg-amber-500/10 px-2 py-0.5 text-amber-700 dark:text-amber-400"
                        data-testid={`detect-pair-score-${pair.source_id}`}
                      >
                        {scorePct}%
                      </span>
                    </div>
                    <div className="mt-2 flex items-center justify-end gap-2">
                      {isConfirming ? (
                        <>
                          <span className="mr-1 text-xs text-muted-foreground">
                            ¿Confirmar?
                          </span>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setConfirmingId(null)}
                          >
                            No
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => handleConfirm(pair)}
                            data-testid={`detect-confirm-${pair.source_id}`}
                          >
                            Sí
                          </Button>
                        </>
                      ) : (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDismiss(pair)}
                          >
                            Descartar
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => setConfirmingId(pair.source_id)}
                          >
                            Confirmar
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )
        ) : null}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cerrar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}