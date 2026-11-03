"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function ProfilePage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [message, setMessage] = useState({ text: "", type: "" });
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Проверяем авторизацию
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/auth/login");
      return;
    }

    // Подтягиваем данные из локального хранилища
    const savedEmail = localStorage.getItem("userEmail") || "";
    const savedName = localStorage.getItem("userName") || savedEmail.split('@')[0] || "";
    const savedPhone = localStorage.getItem("userPhone") || "";

    setEmail(savedEmail);
    setName(savedName);
    setPhone(savedPhone);
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage({ text: "", type: "" });

    try {
      // Имитация задержки запроса к API
      await new Promise((resolve) => setTimeout(resolve, 600));

      // Сохраняем введенные данные в localStorage
      localStorage.setItem("userName", name);
      localStorage.setItem("userPhone", phone);
      
      // Даем сигнал шапке сайта (Header), что имя изменилось
      window.dispatchEvent(new Event("auth-change"));

      setMessage({ text: "Данные профиля успешно обновлены!", type: "success" });
    } catch (error) {
      setMessage({ text: "Произошла ошибка при сохранении", type: "error" });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-72px)] items-start justify-center bg-gray-900 pt-12 p-4">
      <div className="w-full max-w-2xl p-8 bg-gray-800 rounded-2xl shadow-2xl border border-gray-700 text-white">
        
        {/* Заголовок и Аватар */}
        <div className="flex items-center gap-5 mb-8 pb-6 border-b border-gray-700">
          <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center text-3xl font-bold shadow-lg shadow-green-500/20">
            {name ? name.charAt(0).toUpperCase() : "U"}
          </div>
          <div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">Личный кабинет</h1>
            <p className="text-gray-400 mt-1">Управление личными данными</p>
          </div>
        </div>

        {/* Уведомления */}
        {message.text && (
          <div className={`mb-6 p-4 rounded-lg text-sm font-medium border ${message.type === 'success' ? 'bg-green-500/10 text-green-400 border-green-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
            {message.text}
          </div>
        )}

        {/* Форма */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-300">Имя пользователя</label>
              <input 
                type="text" 
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full p-3 rounded-xl bg-gray-900/50 border border-gray-600 focus:border-green-400 focus:ring-1 focus:ring-green-400 focus:outline-none transition-all placeholder-gray-500"
                placeholder="Например: Алексей"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2 text-gray-300">Номер телефона</label>
              <input 
                type="tel" 
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full p-3 rounded-xl bg-gray-900/50 border border-gray-600 focus:border-green-400 focus:ring-1 focus:ring-green-400 focus:outline-none transition-all placeholder-gray-500"
                placeholder="+7 (___) ___-__-__"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium mb-2 text-gray-300">Email (Логин)</label>
              <input 
                type="email" 
                value={email}
                disabled
                className="w-full p-3 rounded-xl bg-gray-900/80 border border-gray-700 text-gray-400 cursor-not-allowed"
                title="Для смены email обратитесь в поддержку"
              />
              <p className="text-xs text-gray-500 mt-2">Email используется для входа и не может быть изменен напрямую.</p>
            </div>
          </div>

          <div className="pt-6 flex justify-end">
            <button 
              type="submit" 
              disabled={isLoading}
              className="px-8 py-3 bg-green-500 hover:bg-green-400 text-gray-900 font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(34,197,94,0.3)] hover:shadow-[0_0_25px_rgba(34,197,94,0.5)] disabled:opacity-50 disabled:shadow-none"
            >
              {isLoading ? "Сохранение..." : "Сохранить изменения"}
            </button>
          </div>
        </form>

      </div>
    </div>
  );
}