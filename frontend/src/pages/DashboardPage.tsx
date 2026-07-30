import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { IncomeExpenseChart } from "@/components/dashboard/IncomeExpenseChart"
import { CategorySummaryTable } from "@/components/dashboard/CategorySummaryTable"
import { PatrimonialSummaryTable } from "@/components/dashboard/PatrimonialSummaryTable"
import {
  REPORT_PERIODS,
  REPORT_PERIODS_COUNTS,
  type Account,
  type CategorySummary,
  type IncomeExpenseSummary,
  type ReportFilters,
  type ReportPeriod,
} from "@/lib/schemas"
import {
  fetchAccounts,
  fetchCategorySummary,
  fetchIncomeExpenseSummary,
} from "@/lib/api"
import { extractApiError } from "@/lib/errors"

const PERIOD_LABEL_SINGULAR: Record<ReportPeriod, string> = {
  week: "semana",
  month: "mes",
  year: "año",
}

const PERIOD_LABEL_PLURAL: Record<ReportPeriod, string> = {
  week: "semanas",
  month: "meses",
  year: "años",
}

export function DashboardPage() {
  const [summary, setSummary] = useState<IncomeExpenseSummary | null>(null)
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<ReportFilters>({
    period: "month",
    periods_count: 6,
  })
  const [catSummary, setCatSummary] = useState<CategorySummary | null>(null)
  const [catLoading, setCatLoading] = useState(true)
  const [catError, setCatError] = useState<string | null>(null)
  const [catFilters, setCatFilters] = useState<ReportFilters>({
    period: "month",
    periods_count: 6,
  })
  const [patSummary, setPatSummary] = useState<CategorySummary | null>(null)
  const [patLoading, setPatLoading] = useState(true)
  const [patError, setPatError] = useState<string | null>(null)
  const [patFilters, setPatFilters] = useState<ReportFilters>({
    period: "month",
    periods_count: 6,
  })

  useEffect(() => {
    let active = true
    fetchAccounts()
      .then((data) => {
        if (active) setAccounts(data)
      })
      .catch(() => {
        // accounts load failure is non-fatal for the summary
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    let active = true
    fetchIncomeExpenseSummary(filters)
      .then((data) => {
        if (active) {
          setSummary(data)
          setError(null)
          setLoading(false)
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(
            extractApiError(err) ?? "No pudimos cargar el resumen",
          )
          setLoading(false)
        }
      })
    return () => {
      active = false
    }
  }, [filters])

  useEffect(() => {
    let active = true
    fetchCategorySummary(catFilters)
      .then((data) => {
        if (active) {
          setCatSummary(data)
          setCatError(null)
          setCatLoading(false)
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setCatError(
            extractApiError(err) ?? "No pudimos cargar el resumen por categoría",
          )
          setCatLoading(false)
        }
      })
    return () => {
      active = false
    }
  }, [catFilters])

  useEffect(() => {
    let active = true
    fetchCategorySummary(patFilters, { onlyPatrimonial: true })
      .then((data) => {
        if (active) {
          setPatSummary(data)
          setPatError(null)
          setPatLoading(false)
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setPatError(
            extractApiError(err) ?? "No pudimos cargar el resumen patrimonial",
          )
          setPatLoading(false)
        }
      })
    return () => {
      active = false
    }
  }, [patFilters])

  function updatePeriod(value: string) {
    setLoading(true)
    setFilters((prev) => ({ ...prev, period: value as ReportPeriod }))
  }

  function updatePeriodsCount(value: string) {
    setLoading(true)
    setFilters((prev) => ({ ...prev, periods_count: Number(value) }))
  }

  function updateAccount(value: string) {
    setLoading(true)
    setFilters((prev) => ({
      ...prev,
      account_id: value === "all" ? undefined : Number(value),
    }))
  }

  function updateCatPeriod(value: string) {
    setCatLoading(true)
    setCatFilters((prev) => ({ ...prev, period: value as ReportPeriod }))
  }

  function updateCatPeriodsCount(value: string) {
    setCatLoading(true)
    setCatFilters((prev) => ({ ...prev, periods_count: Number(value) }))
  }

  function updateCatAccount(value: string) {
    setCatLoading(true)
    setCatFilters((prev) => ({
      ...prev,
      account_id: value === "all" ? undefined : Number(value),
    }))
  }

  function updatePatPeriod(value: string) {
    setPatLoading(true)
    setPatFilters((prev) => ({ ...prev, period: value as ReportPeriod }))
  }

  function updatePatPeriodsCount(value: string) {
    setPatLoading(true)
    setPatFilters((prev) => ({ ...prev, periods_count: Number(value) }))
  }

  function updatePatAccount(value: string) {
    setPatLoading(true)
    setPatFilters((prev) => ({
      ...prev,
      account_id: value === "all" ? undefined : Number(value),
    }))
  }

  const periodLabel =
    filters.periods_count === 1
      ? PERIOD_LABEL_SINGULAR[filters.period]
      : PERIOD_LABEL_PLURAL[filters.period]
  const description = `Últimos ${filters.periods_count} ${periodLabel} (excluye transferencias y movimientos patrimoniales)`

  const catPeriodLabel =
    catFilters.periods_count === 1
      ? PERIOD_LABEL_SINGULAR[catFilters.period]
      : PERIOD_LABEL_PLURAL[catFilters.period]
  const catDescription = `Totales por categoría en los últimos ${catFilters.periods_count} ${catPeriodLabel} (excluye transferencias)`

  const patPeriodLabel =
    patFilters.periods_count === 1
      ? PERIOD_LABEL_SINGULAR[patFilters.period]
      : PERIOD_LABEL_PLURAL[patFilters.period]
  const patDescription = `Movimientos de categorías patrimoniales en los últimos ${patFilters.periods_count} ${patPeriodLabel} (excluye transferencias)`

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Resumen de tus ingresos y egresos por periodo.
        </p>
      </div>

      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Categorías por periodo</CardTitle>
          <CardDescription>{catDescription}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-end gap-3">
            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Periodo</label>
              <Select
                value={catFilters.period}
                onValueChange={updateCatPeriod}
              >
                <SelectTrigger className="w-[160px]" data-testid="cat-period-select">
                  <SelectValue placeholder="Periodo" />
                </SelectTrigger>
                <SelectContent>
                  {REPORT_PERIODS.map((p) => (
                    <SelectItem key={p.value} value={p.value}>
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Cantidad</label>
              <Select
                value={String(catFilters.periods_count)}
                onValueChange={updateCatPeriodsCount}
              >
                <SelectTrigger className="w-[120px]" data-testid="cat-periods-count-select">
                  <SelectValue placeholder="Cantidad" />
                </SelectTrigger>
                <SelectContent>
                  {REPORT_PERIODS_COUNTS.map((p) => (
                    <SelectItem key={p.value} value={String(p.value)}>
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Cuenta</label>
              <Select
                value={
                  catFilters.account_id != null
                    ? String(catFilters.account_id)
                    : "all"
                }
                onValueChange={updateCatAccount}
              >
                <SelectTrigger className="w-[160px]" data-testid="cat-account-select">
                  <SelectValue placeholder="Todas" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  {accounts
                    .filter((a) => a.is_active)
                    .map((a) => (
                      <SelectItem key={a.id} value={String(a.id)}>
                        {a.name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Separator />

          {catError ? (
            <Alert variant="destructive">
              <AlertDescription>{catError}</AlertDescription>
            </Alert>
          ) : catLoading ? (
            <div className="flex items-center justify-center py-16 text-muted-foreground">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Cargando…
            </div>
          ) : catSummary ? (
            <CategorySummaryTable summary={catSummary} />
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Ingresos vs Egresos</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-end gap-3">
            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Periodo</label>
              <Select
                value={filters.period}
                onValueChange={updatePeriod}
              >
                <SelectTrigger className="w-[160px]" data-testid="report-period-select">
                  <SelectValue placeholder="Periodo" />
                </SelectTrigger>
                <SelectContent>
                  {REPORT_PERIODS.map((p) => (
                    <SelectItem key={p.value} value={p.value}>
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Cantidad</label>
              <Select
                value={String(filters.periods_count)}
                onValueChange={updatePeriodsCount}
              >
                <SelectTrigger className="w-[120px]" data-testid="report-periods-count-select">
                  <SelectValue placeholder="Cantidad" />
                </SelectTrigger>
                <SelectContent>
                  {REPORT_PERIODS_COUNTS.map((p) => (
                    <SelectItem key={p.value} value={String(p.value)}>
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Cuenta</label>
              <Select
                value={
                  filters.account_id != null
                    ? String(filters.account_id)
                    : "all"
                }
                onValueChange={updateAccount}
              >
                <SelectTrigger className="w-[160px]" data-testid="report-account-select">
                  <SelectValue placeholder="Todas" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  {accounts
                    .filter((a) => a.is_active)
                    .map((a) => (
                      <SelectItem key={a.id} value={String(a.id)}>
                        {a.name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Separator />

          {loading ? (
            <div className="flex items-center justify-center py-16 text-muted-foreground">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Cargando…
            </div>
          ) : summary ? (
            <IncomeExpenseChart summary={summary} />
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Movimientos patrimoniales por periodo</CardTitle>
          <CardDescription>{patDescription}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap items-end gap-3">
            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Periodo</label>
              <Select
                value={patFilters.period}
                onValueChange={updatePatPeriod}
              >
                <SelectTrigger className="w-[160px]" data-testid="pat-period-select">
                  <SelectValue placeholder="Periodo" />
                </SelectTrigger>
                <SelectContent>
                  {REPORT_PERIODS.map((p) => (
                    <SelectItem key={p.value} value={p.value}>
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Cantidad</label>
              <Select
                value={String(patFilters.periods_count)}
                onValueChange={updatePatPeriodsCount}
              >
                <SelectTrigger className="w-[120px]" data-testid="pat-periods-count-select">
                  <SelectValue placeholder="Cantidad" />
                </SelectTrigger>
                <SelectContent>
                  {REPORT_PERIODS_COUNTS.map((p) => (
                    <SelectItem key={p.value} value={String(p.value)}>
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-sm font-medium">Cuenta</label>
              <Select
                value={
                  patFilters.account_id != null
                    ? String(patFilters.account_id)
                    : "all"
                }
                onValueChange={updatePatAccount}
              >
                <SelectTrigger className="w-[160px]" data-testid="pat-account-select">
                  <SelectValue placeholder="Todas" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todas</SelectItem>
                  {accounts
                    .filter((a) => a.is_active)
                    .map((a) => (
                      <SelectItem key={a.id} value={String(a.id)}>
                        {a.name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Separator />

          {patError ? (
            <Alert variant="destructive">
              <AlertDescription>{patError}</AlertDescription>
            </Alert>
          ) : patLoading ? (
            <div className="flex items-center justify-center py-16 text-muted-foreground">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Cargando…
            </div>
          ) : patSummary ? (
            <PatrimonialSummaryTable summary={patSummary} />
          ) : null}
        </CardContent>
      </Card>
    </div>
  )
}