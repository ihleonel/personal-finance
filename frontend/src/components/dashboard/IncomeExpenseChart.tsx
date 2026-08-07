import {
  Bar,
  BarChart as RechartsBarChart,
  CartesianGrid,
  XAxis,
  YAxis,
} from "recharts"

import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
import type { IncomeExpenseSummary } from "@/lib/schemas"
import { formatAmount } from "@/lib/format"

type IncomeExpenseChartProps = {
  summary: IncomeExpenseSummary
}

const chartConfig = {
  income: {
    label: "Ingresos",
    color: "var(--chart-1)",
  },
  expenseFixed: {
    label: "Costos fijos",
    color: "var(--chart-2)",
  },
  expenseVariable: {
    label: "Costos variables",
    color: "var(--chart-5)",
  },
} satisfies ChartConfig

function computeXLabel(period: string, key: string): string {
  if (period === "month") {
    const [y, m] = key.split("-")
    return `${m}/${y}`
  }
  if (period === "year") {
    return key
  }
  if (period === "week") {
    const [y, w] = key.split("-W")
    return `${w}/${y}`
  }
  return key
}

type RoundedBarOptions = {
  isTopOfStack?: boolean
}

function roundedBarShape(props: unknown, opts: RoundedBarOptions = {}) {
  const isTopOfStack = opts.isTopOfStack ?? true
  const p = props as {
    isPartial?: boolean
    x?: number
    y?: number
    width?: number
    height?: number
    fill?: string
    payload?: { isPartial?: boolean }
  }
  const isPartial = p.isPartial ?? p.payload?.isPartial
  const x = p.x ?? 0
  const y = p.y ?? 0
  const width = p.width ?? 0
  const height = p.height ?? 0
  const fill = p.fill ?? "currentColor"
  const r = 4
  const tl = isTopOfStack ? r : 0
  const tr = isTopOfStack ? r : 0
  const br = isTopOfStack ? 0 : r
  const bl = isTopOfStack ? 0 : r
  const d = roundedRectPath(x, y, width, height, tl, tr, br, bl)
  if (isPartial) {
    return (
      <path
        d={d}
        fill={fill}
        fillOpacity={0.55}
        stroke={fill}
        strokeDasharray="4 4"
        strokeWidth={1.5}
      />
    )
  }
  return <path d={d} fill={fill} />
}

function roundedRectPath(
  x: number,
  y: number,
  w: number,
  h: number,
  tl: number,
  tr: number,
  br: number,
  bl: number,
): string {
  if (w <= 0 || h <= 0) return ""
  const maxR = Math.min(w / 2, h / 2)
  const tlr = Math.min(tl, maxR)
  const trr = Math.min(tr, maxR)
  const brr = Math.min(br, maxR)
  const blr = Math.min(bl, maxR)
  const x0 = x
  const x1 = x + w
  const y0 = y
  const y1 = y + h
  return [
    `M ${x0 + tlr} ${y0}`,
    `H ${x1 - trr}`,
    trr > 0 ? `A ${trr} ${trr} 0 0 1 ${x1} ${y0 + trr}` : "",
    `V ${y1 - brr}`,
    brr > 0 ? `A ${brr} ${brr} 0 0 1 ${x1 - brr} ${y1}` : "",
    `H ${x0 + blr}`,
    blr > 0 ? `A ${blr} ${blr} 0 0 1 ${x0} ${y1 - blr}` : "",
    `V ${y0 + tlr}`,
    tlr > 0 ? `A ${tlr} ${tlr} 0 0 1 ${x0 + tlr} ${y0}` : "",
    "Z",
  ]
    .filter(Boolean)
    .join(" ")
}

function shapeForStack(isTopOfStack: boolean) {
  return (props: unknown) => roundedBarShape(props, { isTopOfStack })
}

export function IncomeExpenseChart({ summary }: IncomeExpenseChartProps) {
  const data = [
    ...summary.buckets.map((b) => ({
      label: b.label,
      xLabel: computeXLabel(summary.period, b.key),
      income: Number(b.income),
      expenseFixed: Number(b.expense_fixed ?? "0"),
      expenseVariable: Number(b.expense_variable ?? "0"),
      isPartial: false,
    })),
    {
      label: summary.current_period.label,
      xLabel: computeXLabel(summary.period, summary.current_period.key),
      income: Number(summary.current_period.income),
      expenseFixed: Number(summary.current_period.expense_fixed ?? "0"),
      expenseVariable: Number(summary.current_period.expense_variable ?? "0"),
      isPartial: true,
    },
  ]

  const labelFor = (name: string) => {
    if (name === "income") return "Ingresos"
    if (name === "expenseFixed") return "Costos fijos"
    if (name === "expenseVariable") return "Costos variables"
    return name
  }

  return (
    <div data-testid="income-expense-chart">
      <ChartContainer config={chartConfig} className="aspect-[16/7] w-full">
        <RechartsBarChart data={data} barCategoryGap="20%">
          <CartesianGrid vertical={false} strokeDasharray="3 3" />
          <XAxis
            dataKey="xLabel"
            tickLine={false}
            axisLine={false}
            tickMargin={8}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            width={110}
            tickFormatter={(value: number) => formatAmount(value)}
          />
          <ChartTooltip
            content={
              <ChartTooltipContent
                labelFormatter={(_, payload) => {
                  const item = payload?.[0]
                  const isPartial = item?.payload?.isPartial
                  return (
                    <div className="flex items-center gap-2">
                      <span>{item?.payload?.label}</span>
                      {isPartial ? (
                        <span className="rounded-full border border-dashed border-amber-500/60 bg-amber-500/10 px-1.5 py-0.5 text-[10px] text-amber-700 dark:text-amber-400">
                          En curso
                        </span>
                      ) : null}
                    </div>
                  )
                }}
                formatter={(value, name) => (
                  <div className="flex flex-1 justify-between leading-none">
                    <span className="text-muted-foreground">
                      {labelFor(String(name))}
                    </span>
                    <span className="font-mono font-medium text-foreground tabular-nums">
                      {formatAmount(Number(value))}
                    </span>
                  </div>
                )}
              />
            }
          />
          <ChartLegend
            content={<ChartLegendContent />}
            payload={[
              { value: "Ingresos", type: "square", id: "income", color: "var(--chart-1)" },
              {
                value: "Costos fijos",
                type: "square",
                id: "expenseFixed",
                color: "var(--chart-2)",
              },
              {
                value: "Costos variables",
                type: "square",
                id: "expenseVariable",
                color: "var(--chart-5)",
              },
            ]}
          />
          <Bar
            dataKey="income"
            fill="var(--color-income)"
            shape={shapeForStack(true)}
          />
          <Bar
            dataKey="expenseFixed"
            stackId="expense"
            fill="var(--color-expenseFixed)"
            shape={shapeForStack(false)}
          />
          <Bar
            dataKey="expenseVariable"
            stackId="expense"
            fill="var(--color-expenseVariable)"
            shape={shapeForStack(true)}
          />
        </RechartsBarChart>
      </ChartContainer>

      <p className="mt-2 text-center text-xs text-muted-foreground">
        Periodo en curso (parcial): {summary.current_period.days_elapsed} de{" "}
        {summary.current_period.days_total} días
      </p>
    </div>
  )
}
