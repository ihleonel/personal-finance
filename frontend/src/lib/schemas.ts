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
