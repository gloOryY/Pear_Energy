import "./globals.css";
import dynamic from "next/dynamic";
import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import { Providers } from "@/components/providers";

// Отключаем SSR для Header — он будет собираться сразу в браузере без конфликтов с localStorage
const Header = dynamic(() => import("@/components/layout/Header"), {
  ssr: false,
  loading: () => (
    <header className="bg-gray-800 text-white p-4 h-[72px] border-b border-gray-700" />
  ),
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className="dark" suppressHydrationWarning>
      <body className="min-h-screen bg-gray-950 text-white" suppressHydrationWarning>
        <Header />
        {children}
      </body>
    </html>
  );
}

export const metadata = {
  title: "Pear Energy",
  description: "Сеть зарядных станций",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" className="dark" suppressHydrationWarning>
      <body className="min-h-screen flex flex-col" suppressHydrationWarning>
        <Providers>
          <Header />
          <main className="flex-1">{children}</main>
          <Footer />
        </Providers>
      </body>
    </html>
  );
}