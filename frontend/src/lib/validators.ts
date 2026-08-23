import { z } from 'zod';

export const loginSchema = z.object({
  email: z.string().email('Некорректный email'),
  password: z.string().min(1, 'Введите пароль'),
});

export const registerSchema = z.object({
  full_name: z.string().min(2, 'Минимум 2 символа'),
  phone: z.string().regex(/^\+7\d{10}$/, '+79001234567'),
  email: z.string().email('Некорректный email'),
  password: z.string().min(8, 'Минимум 8 символов'),
});

export const profileSchema = z.object({
  full_name: z.string().min(2).optional(),
  phone: z.string().regex(/^\+7\d{10}$/).optional(),
  email: z.string().email().optional(),
});

export type LoginValues = z.infer<typeof loginSchema>;
export type RegisterValues = z.infer<typeof registerSchema>;
