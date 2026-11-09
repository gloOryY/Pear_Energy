"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

export default function Header() {
  const router = useRouter();
  const [userDisplayName, setUserDisplayName] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const checkAuth = () => {
      const token = localStorage.getItem("token");
      const email = localStorage.getItem("userEmail");
      const name = localStorage.getItem("userName");

      if (token && email) {
        setUserDisplayName(name || email.split("@")[0]);
        setUserEmail(email);
      } else {
        setUserDisplayName(null);
        setUserEmail(null);
      }
    };

    checkAuth();
    window.addEventListener("auth-change", checkAuth);
    return () => window.removeEventListener("auth-change", checkAuth);
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("userEmail");
    localStorage.removeItem("userName");
    localStorage.removeItem("userPhone");
    window.dispatchEvent(new Event("auth-change"));
    router.push("/");
  };

  return (
    <header
      suppressHydrationWarning
      className="bg-gray-800 text-white p-4 flex justify-between items-center shadow-lg border-b border-gray-700"
    >
      <Link
        href="/"
        className="text-xl font-bold text-green-400 flex items-center gap-2 hover:text-green-300 transition-colors"
      >
        <span>⚡ Pear Energy</span>
      </Link>

      <nav className="flex items-center gap-6">
        <Link
          href="/map"
          className="text-sm font-medium text-gray-300 hover:text-green-400 transition"
        >
          Карта
        </Link>

        {mounted ? (
          userDisplayName ? (
            <div className="flex items-center gap-4 ml-2 pl-6 border-l border-gray-600">
              {userEmail === "admin@example.com" && (
                <Link
                  href="/admin/stations"
                  className="px-3 py-1.5 bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500 hover:text-gray-900 rounded-lg text-sm font-bold transition-colors"
                >
                  Панель управления
                </Link>
              )}

              <Link
                href="/profile"
                className="group flex items-center gap-3 hover:bg-gray-700 py-1.5 px-3 rounded-lg transition-all"
              >
                <div className="w-8 h-8 bg-gray-700 group-hover:bg-green-500 rounded-full flex items-center justify-center text-green-400 group-hover:text-gray-900 font-bold transition-colors">
                  {userDisplayName.charAt(0).toUpperCase()}
                </div>
                <span className="hidden sm:inline text-sm font-medium text-gray-200 group-hover:text-white transition-colors">
                  Здравствуйте, {userDisplayName}
                </span>
              </Link>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-500/10 hover:bg-red-500 text-red-400 hover:text-white rounded-lg text-sm font-medium transition-colors"
              >
                Выйти
              </button>
            </div>
          ) : (
            <div className="flex gap-3 ml-2 pl-6 border-l border-gray-600">
              <Link
                href="/auth/login"
                className="px-5 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors"
              >
                Войти
              </Link>
              <Link
                href="/auth/register"
                className="px-5 py-2 bg-green-500 hover:bg-green-400 text-gray-900 rounded-lg text-sm font-bold transition-colors"
              >
                Регистрация
              </Link>
            </div>
          )
        ) : (
          <div className="w-48 h-9 bg-gray-700/60 animate-pulse rounded-lg ml-2" />
        )}
      </nav>
    </header>
  );
}