import { z } from "zod"

export const loginSchema = z.object({
  email: z.string().min(1, "El email es obligatorio").email("Email inválido"),
  password: z.string().min(1, "La contraseña es obligatoria"),
})

export type LoginInput = z.infer<typeof loginSchema>

export const registerSchema = z
  .object({
    first_name: z
      .string()
      .min(1, "El nombre es obligatorio")
      .max(50, "Máximo 50 caracteres"),
    last_name: z
      .string()
      .min(1, "El apellido es obligatorio")
      .max(50, "Máximo 50 caracteres"),
    email: z.string().min(1, "El email es obligatorio").email("Email inválido"),
    password: z
      .string()
      .min(8, "La contraseña debe tener al menos 8 caracteres"),
    confirm_password: z.string().min(1, "Confirmá la contraseña"),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Las contraseñas no coinciden",
    path: ["confirm_password"],
  })

export type RegisterInput = z.infer<typeof registerSchema>

export const profileSchema = z.object({
  first_name: z
    .string()
    .min(1, "El nombre es obligatorio")
    .max(150, "Máximo 150 caracteres"),
  last_name: z
    .string()
    .min(1, "El apellido es obligatorio")
    .max(150, "Máximo 150 caracteres"),
})

export type ProfileInput = z.infer<typeof profileSchema>

export const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, "La contraseña actual es obligatoria"),
    new_password: z
      .string()
      .min(8, "La contraseña debe tener al menos 8 caracteres"),
    confirm_password: z.string().min(1, "Confirmá la nueva contraseña"),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    message: "Las contraseñas no coinciden",
    path: ["confirm_password"],
  })

export type ChangePasswordInput = z.infer<typeof changePasswordSchema>

export type AuthUser = {
  id: number
  email: string
  first_name: string
  last_name: string
  is_active: boolean
}

export type AuthTokens = {
  access: string
  refresh: string
}

export type AuthSession = {
  user: AuthUser
  tokens: AuthTokens
}

export const ACCOUNT_TYPES = [
  { value: "cash", label: "Efectivo" },
  { value: "bank", label: "Banco" },
  { value: "credit_card", label: "Tarjeta de crédito" },
  { value: "savings", label: "Ahorro" },
  { value: "investment", label: "Inversión" },
  { value: "other", label: "Otra" },
] as const

export const CURRENCIES = [
  { value: "ARS", label: "Peso argentino" },
  { value: "USD", label: "Dólar estadounidense" },
  { value: "EUR", label: "Euro" },
] as const

export const accountSchema = z.object({
  name: z
    .string()
    .min(1, "El nombre de la cuenta es obligatorio")
    .max(100, "Asegúrate de que el nombre no tenga más de 100 caracteres."),
  account_type: z.enum([
    "cash",
    "bank",
    "credit_card",
    "savings",
    "investment",
    "other",
  ]),
  currency: z.enum(["ARS", "USD", "EUR"]),
  initial_balance: z.string(),
})

export type AccountInput = z.infer<typeof accountSchema>

export type Account = {
  id: number
  owner_id: number
  name: string
  account_type: string
  currency: string
  initial_balance: string
  is_active: boolean
}

export const CATEGORY_KINDS = [
  { value: "income", label: "Ingreso" },
  { value: "expense", label: "Egreso" },
] as const

export const categorySchema = z.object({
  name: z
    .string()
    .min(1, "El nombre de la categoría es obligatorio")
    .max(100, "Asegúrate de que el nombre no tenga más de 100 caracteres."),
  kind: z.enum(["income", "expense"]),
  include_in_summaries: z.boolean().default(true),
  is_fixed: z.boolean().default(false),
})

export type CategoryInput = z.infer<typeof categorySchema>

export type Category = {
  id: number
  owner_id: number
  name: string
  kind: string
  include_in_summaries: boolean
  is_fixed: boolean
  is_active: boolean
}

export const RULE_MATCH_TYPES = [
  { value: "contains", label: "Contiene" },
  { value: "equals", label: "Es igual a" },
] as const

export const categorizationRuleSchema = z.object({
  pattern: z
    .string()
    .min(1, "El patrón es obligatorio")
    .max(120, "Asegúrate de que el patrón no tenga más de 120 caracteres."),
  match_type: z.enum(["contains", "equals"]),
  category_id: z.number().min(1, "La categoría es obligatoria."),
  kind: z.enum(["income", "expense"]),
  priority: z.number().int().min(0, "La prioridad debe ser un número no negativo."),
})

export type CategorizationRuleInput = z.infer<typeof categorizationRuleSchema>

export type CategorizationRuleUpdateInput = Partial<CategorizationRuleInput>

export const categoryRuleFormSchema = categorizationRuleSchema.pick({
  pattern: true,
  match_type: true,
  priority: true,
})

export type CategoryRuleFormInput = z.infer<typeof categoryRuleFormSchema>

export type CategorizationRule = {
  id: number
  owner_id: number
  pattern: string
  match_type: string
  category_id: number
  kind: string
  priority: number
  is_active: boolean
}

export type SuggestCategoryResult = {
  category_id: number | null
  category_name: string | null
}

export const TRANSACTION_KINDS = [
  { value: "income", label: "Ingreso" },
  { value: "expense", label: "Egreso" },
] as const

export type Transaction = {
  id: number
  owner_id: number
  account_id: number
  category_id: number | null
  kind: string
  amount: string
  date: string
  description: string
  created_at: string
  suggested_category_id?: number | null
}

export type TransactionFilters = {
  account_id?: number
  kind?: string
  category_id?: number
  category_id_isnull?: boolean
  date_from?: string
  date_to?: string
  description?: string
}

export type PaginatedResponse<T> = {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export const transactionSchema = z.object({
  account_id: z.number({ error: "La cuenta es obligatoria." }),
  kind: z.enum(["income", "expense"]),
  amount: z.string().min(1, "El monto es obligatorio."),
  date: z.string().min(1, "La fecha es obligatoria."),
  category_id: z.number().optional().nullable(),
  description: z
    .string()
    .max(255, "La descripción no puede tener más de 255 caracteres.")
    .optional(),
})
export type TransactionInput = z.infer<typeof transactionSchema>

export type ImportSkippedRow = {
  row_number: number
  external_reference: string
  reason: string
}

export type ImportErrorRow = {
  row_number: number
  field: string
  message: string
}

export type ImportSummary = {
  total: number
  created: number
  skipped: number
  errors: number
}

export type ImportTransactionResult = {
  created: Transaction[]
  skipped: ImportSkippedRow[]
  errors: ImportErrorRow[]
  summary: ImportSummary
}

export const transactionUpdateSchema = z.object({
  amount: z.string().min(1, "El monto es obligatorio.").optional(),
  date: z.string().min(1, "La fecha es obligatoria.").optional(),
  description: z
    .string()
    .max(255, "La descripción no puede tener más de 255 caracteres.")
    .optional(),
  category_id: z.number().nullable().optional(),
})
export type TransactionUpdateInput = z.infer<typeof transactionUpdateSchema>

export type BulkAssignCategoryInput = {
  transaction_ids: number[]
  category_id: number | null
}

export type BulkAssignCategoryResult = {
  updated_count: number
  skipped_ids: number[]
  skipped_kinds: number[]
}

export const REPORT_PERIODS = [
  { value: "week", label: "Semanas" },
  { value: "month", label: "Meses" },
  { value: "year", label: "Años" },
] as const

export const REPORT_PERIODS_COUNTS = [
  { value: 1, label: "1" },
  { value: 2, label: "2" },
  { value: 3, label: "3" },
  { value: 4, label: "4" },
  { value: 5, label: "5" },
  { value: 6, label: "6" },
  { value: 7, label: "7" },
  { value: 8, label: "8" },
  { value: 9, label: "9" },
  { value: 10, label: "10" },
  { value: 11, label: "11" },
  { value: 12, label: "12" },
] as const

export type ReportPeriod = "week" | "month" | "year"

export type ReportFilters = {
  period: ReportPeriod
  periods_count: number
  account_id?: number
}

export type PeriodBucket = {
  key: string
  label: string
  income: string
  expense: string
  net: string
  balance_movement_inflow?: string
  balance_movement_outflow?: string
  balance_movement_net?: string
}

export type CurrentPeriod = PeriodBucket & {
  is_partial: boolean
  days_elapsed: number
  days_total: number
  balance_movement_inflow?: string
  balance_movement_outflow?: string
  balance_movement_net?: string
}

export type IncomeExpenseSummary = {
  period: string
  periods_count: number
  buckets: PeriodBucket[]
  current_period: CurrentPeriod
}

export type CategoryPeriodColumn = {
  key: string
  label: string
  is_partial: boolean
  days_elapsed: number
  days_total: number
}

export type CategoryRow = {
  category_id: number | null
  name: string
  kind: string
  is_uncategorized: boolean
  is_active: boolean
  include_in_summaries?: boolean
  amounts: string[]
}

export type CategorySummary = {
  period: string
  periods_count: number
  columns: CategoryPeriodColumn[]
  rows: CategoryRow[]
  totals: CategoryTotals
}

export type CategoryTotals = {
  amounts: string[]
  accumulated: string[]
}
