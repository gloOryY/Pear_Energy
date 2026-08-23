import type { Metadata } from 'next';
import './globals.css';
import { Providers } from '../components/providers';
import Header from '../components/layout/Header';
import Footer from '../components/layout/Footer';

export const metadata: Metadata = {
  title: 'ChargePoint Road — Зарядные станции для электромобилей',
  description: 'Найдите и забронируйте зарядную станцию Type 2 рядом с вами. Оплата через СБП, карта или баланс. Поддержка 24/7.',
  viewport: 'width=device-width, initial-scale=1',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className="dark">
      <body className="min-h-screen flex flex-col">
        <Providers>
          <Header />
          <main className="flex-1">{children}</main>
          <Footer />
        </Providers>
      </body>
    </html>
  );
}
