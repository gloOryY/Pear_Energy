import type { Metadata } from "next";
import Header from "@/components/layout/Header";
import Providers from "@/components/Providers"; // если у вас используется Providers
import "./globals.css";

export const metadata: Metadata = {
  title: "Pear Energy",
  description: "Система мониторинга и управления зарядными станциями",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" className="dark" suppressHydrationWarning>
      <body className="min-h-screen bg-gray-950 text-white" suppressHydrationWarning>
        <Header />
        {children}
      </body>
    </html>
  );
}