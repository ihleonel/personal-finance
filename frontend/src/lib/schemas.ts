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
