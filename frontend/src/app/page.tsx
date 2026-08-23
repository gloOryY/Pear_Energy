'use client';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { BatteryCharging, CreditCard, CalendarClock, BadgeCheck, Headphones, MapPin, Search, PlugZap, Hotel, ArrowRight } from 'lucide-react';
import { Button } from '../components/ui';

const ADVANTAGES = [
  { icon: CreditCard, title: 'Оплата', text: 'СБП QR, карта или баланс — без привязки карты' },
  { icon: PlugZap, title: 'Type 2', text: 'Стандартный разъём для всех электромобилей' },
  { icon: BadgeCheck, title: 'Надёжность', text: 'Аппаратные лимиты и автостоп при потере связи' },
  { icon: CalendarClock, title: 'Бронирование', text: 'Забронируйте слот на 15 минут' },
  { icon: Headphones, title: 'Поддержка 24/7', text: 'Техподдержка и мониторинг в реальном времени' },
];

const STEPS = [
  { n: 1, text: 'Найдите станцию на карте' },
  { n: 2, text: 'Подключите Type 2 и выберите лимит' },
  { n: 3, text: 'Оплатите через СБП QR' },
  { n: 4, text: 'Заряжайтесь — остановка по лимиту или вручную' },
];

export default function HomePage() {
  const router = useRouter();
  const [q, setQ] = useState('');
  return (
    <div>
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(23,201,158,0.14),transparent_60%)]" />
        <div className="relative max-w-7xl mx-auto px-4 pt-16 pb-20 md:pt-24 md:pb-28">
          <h1 className="text-4xl md:text-6xl font-bold leading-tight max-w-3xl">
            <span className="text-accent">Зарядка</span> электромобиля без стресса
          </h1>
          <p className="mt-5 text-zinc-400 text-lg max-w-xl">
            Найдите свободную станцию Type 2 рядом, забронируйте слот и зарядитесь за минуты. Оплата через СБП QR — без привязки карты. Поддержка 24/7.
          </p>
          <form className="mt-8 flex flex-col sm:flex-row gap-3 max-w-2xl" onSubmit={(e) => { e.preventDefault(); router.push(`/map?q=${encodeURIComponent(q)}`); }}>
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500 size-[20px]" />
              <input value={q} onChange={(e) => setQ(e.target.value)} className="input !pl-12 !py-4 !rounded-2xl text-lg placeholder:text-zinc-500" placeholder="Город, адрес или трасса М-4" aria-label="Поиск" />
            </div>
            <Button type="submit" className="!py-4 !rounded-2xl text-lg">Найти</Button>
          </form>
          <div className="mt-4">
            <Link href="/map" className="inline-flex items-center gap-2 text-accent hover:text-accent-bright font-medium"><MapPin size={18} />Открыть карту</Link>
          </div>
        </div>
      </section>
      <section className="max-w-7xl mx-auto px-4 pb-16">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {ADVANTAGES.map(({ icon: Icon, title, text }) => (
            <div key={title} className="card p-5">
              <Icon className="text-accent mb-3 size-[26px]" />
              <div className="font-semibold mb-1">{title}</div>
              <p className="text-sm text-zinc-400">{text}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="max-w-7xl mx-auto px-4 pb-20">
        <h2 className="text-2xl md:text-3xl font-bold mb-8">Как это работает</h2>
        <ol className="grid gap-4 md:grid-cols-4">
          {STEPS.map((s) => (
            <li key={s.n} className="card p-6">
              <div className="w-10 h-10 rounded-full bg-accent/15 text-accent font-bold flex items-center justify-center mb-4 text-lg">{s.n}</div>
              <p className="text-zinc-300">{s.text}</p>
            </li>
          ))}
        </ol>
      </section>
      <section className="max-w-7xl mx-auto px-4 pb-20">
        <div className="card p-8 md:p-12 bg-gradient-to-br from-graphite-850 to-graphite-900 border-accent/20">
          <div className="flex flex-col md:flex-row md:items-center gap-8">
            <Hotel className="text-accent shrink-0 size-[48px]" />
            <div className="flex-1">
              <h2 className="text-2xl md:text-3xl font-bold">Владельцам отелей и паркингов</h2>
              <p className="mt-3 text-zinc-400">
                Установим станцию под ключ, подключим эквайринг и обеспечим поддержку. Вы получаете 90% дохода, платформа — 10%.
              </p>
            </div>
            <Link href="mailto:partners@chargepoint-road.ru"><Button className="shrink-0 !py-4">Стать партнёром<ArrowRight size={18} className="ml-2 inline" /></Button></Link>
          </div>
        </div>
      </section>
    </div>
  );
}
