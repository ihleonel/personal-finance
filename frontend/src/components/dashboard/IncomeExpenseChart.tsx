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
  expense: {
    label: "Egresos",
    color: "var(--chart-2)",
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

function roundedBarShape(props: unknown) {
  const p = props as {
    isPartial?: boolean
    x?: number
    y?: number
    width?: number
    height?: number
    fill?: string
  }
  if (p.isPartial) {
    return (
      <rect
        x={p.x}
        y={p.y}
        width={p.width}
        height={p.height}
        fill={p.fill}
        fillOpacity={0.55}
        stroke={p.fill}
        strokeDasharray="4 4"
        strokeWidth={1.5}
        rx={4}
        ry={4}
      />
    )
  }
  return (
    <rect
      x={p.x}
      y={p.y}
      width={p.width}
      height={p.height}
      fill={p.fill}
      rx={4}
      ry={4}
    />
  )
}

export function IncomeExpenseChart({ summary }: IncomeExpenseChartProps) {
  const data = [
    ...summary.buckets.map((b) => ({
      label: b.label,
      xLabel: computeXLabel(summary.period, b.key),
      income: Number(b.income),
      expense: Number(b.expense),
      isPartial: false,
    })),
    {
      label: summary.current_period.label,
      xLabel: computeXLabel(summary.period, summary.current_period.key),
      income: Number(summary.current_period.income),
      expense: Number(summary.current_period.expense),
      isPartial: true,
    },
  ]

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
                      {name === "income" ? "Ingresos" : "Egresos"}
                    </span>
                    <span className="font-mono font-medium text-foreground tabular-nums">
                      {formatAmount(Number(value))}
                    </span>
                  </div>
                )}
              />
            }
          />
          <ChartLegend content={<ChartLegendContent />} />
          <Bar
            dataKey="income"
            fill="var(--color-income)"
            shape={roundedBarShape}
          />
          <Bar
            dataKey="expense"
            fill="var(--color-expense)"
            shape={roundedBarShape}
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