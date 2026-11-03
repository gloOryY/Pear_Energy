"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const response = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        throw new Error("Неверный email или пароль");
      }

      const data = await response.json();
      
      // Сохраняем токен и email (чтобы показать его в шапке)
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("userEmail", email);
      
      // Отправляем сигнал, чтобы Header сразу обновил кнопки
      window.dispatchEvent(new Event("auth-change"));
      
      // Плавно возвращаемся на главную
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Ошибка авторизации");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-900">
      <div className="w-full max-w-md p-8 bg-gray-800 rounded-lg shadow-md text-white">
        <h1 className="text-2xl font-bold mb-6 text-center text-green-400">Вход</h1>
        
        {error && <div className="mb-4 p-3 bg-red-500/20 text-red-400 rounded text-sm">{error}</div>}
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-2 rounded bg-gray-700 border border-gray-600 focus:border-green-400 focus:outline-none"
              required 
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Пароль</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-2 rounded bg-gray-700 border border-gray-600 focus:border-green-400 focus:outline-none"
              required 
            />
          </div>
          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full py-2 px-4 bg-green-500 hover:bg-green-600 text-white font-bold rounded transition-colors disabled:opacity-50"
          >
            {isLoading ? "Вход..." : "Войти"}
          </button>
        </form>
        
        <p className="mt-4 text-center text-sm text-gray-400">
          Нет аккаунта? <Link href="/auth/register" className="text-green-400 hover:underline">Зарегистрируйтесь</Link>
        </p>
      </div>
    </div>
  );
}