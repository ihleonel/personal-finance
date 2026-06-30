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
})

export type CategoryInput = z.infer<typeof categorySchema>

export type Category = {
  id: number
  owner_id: number
  name: string
  kind: string
  is_active: boolean
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
  transfer_group_id: string | null
  created_at: string
}

export type TransactionFilters = {
  account_id?: number
  kind?: string
  category_id?: number
  date_from?: string
  date_to?: string
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

export const transferSchema = z
  .object({
    source_account_id: z.number({
      error: "La cuenta de origen es obligatoria.",
    }),
    destination_account_id: z.number({
      error: "La cuenta de destino es obligatoria.",
    }),
    amount: z.string().min(1, "El monto es obligatorio."),
    date: z.string().min(1, "La fecha es obligatoria."),
    category_id: z.number().optional().nullable(),
    description: z
      .string()
      .max(255, "La descripción no puede tener más de 255 caracteres.")
      .optional(),
  })
  .refine((d) => d.source_account_id !== d.destination_account_id, {
    message: "La cuenta de origen y destino no pueden ser la misma.",
    path: ["destination_account_id"],
  })
export type TransferInput = z.infer<typeof transferSchema>

export type TransferOutput = {
  source: Transaction
  destination: Transaction
}

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
