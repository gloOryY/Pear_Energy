'use client';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { LifeBuoy, MapPin, Zap } from 'lucide-react';
import { get } from '../../../lib/api';
import { Badge, Button, Card, Modal, Skeleton, StatusBadge, cn, statusLabel } from '../../../components/ui';
import { money } from '../../../lib/format';
import { StartFlowDialog } from '../../../components/charging/StartFlowDialog';
import { useAuth } from '../../../stores/auth';
import { post } from '../../../lib/api';

interface Review { id: string; rating: number; text: string; created_at: string; author: string | null; }

const LIMIT_PRESETS: Record<string, { label: string; value: number }[]> = {
  kwh: [{ label: '10 кВт⋅ч', value: 10 }, { label: '20 кВт⋅ч', value: 20 }, { label: '40 кВт⋅ч', value: 40 }],
  rub: [{ label: '300 ₽', value: 300 }, { label: '500 ₽', value: 500 }, { label: '1000 ₽', value: 1000 }],
  minutes: [{ label: '30 мин', value: 30 }, { label: '2 ч', value: 120 }, { label: '4 ч', value: 240 }],
};

export default function StationPage() {
  const { id } = useParams<{ id: string }>();
  const user = useAuth();
  const [flowOpen, setFlowOpen] = useState(false);
  const [supportOpen, setSupportOpen] = useState(false);
  const { data: s, isLoading } = useQuery({ queryKey: ['station', id], queryFn: () => get<any>(`stations/${id}`), refetchInterval: 20000 });
  const { data: reviews } = useQuery({ queryKey: ['reviews', id], queryFn: () => get<Review[]>(`stations/${id}/reviews`) });
  if (isLoading || !s) return <div className="max-w-5xl mx-auto px-4 py-10 space-y-4"><Skeleton className="h-64" /><Skeleton className="h-40" /></div>;
  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {s.photos[0] && <img src={s.photos[0]} alt={s.name} className="w-full h-56 md:h-72 object-cover rounded-2xl mb-6" />}
      <div className="grid md:grid-cols-[1fr_340px] gap-6">
        <div>
          <h1 className="text-3xl font-bold">{s.name}</h1>
          <p className="text-zinc-400 mt-1 flex items-center gap-1.5"><MapPin size={16} />{s.address}, {s.city}</p>
          <div className="mt-3"><StatusBadge status={s.status} /></div>
          <Card className="mt-6">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
              <Stat title="Мощность" value={`${s.max_power_kw} кВт`} />
              <Stat title="Разъём" value="Type 2" />
              <Stat title="Тариф" value={`${money(Number(s.tariff_per_kwh))} ₽/кВт⋅ч`} accent />
              <Stat title="Мин. запуск" value={money(Number(s.min_launch_amount)) + ' ₽'} />
            </div>
            <div className="mt-4 text-sm text-zinc-400">
              {s.supports_booking ? <><b className="text-zinc-200">{money(Number(s.booking_amount))} ₽</b> — бронирование на 15 минут. Отмена бесплатно за 15 минут до начала.</> : 'Бронирование недоступно'}
            </div>
            <div className="mt-4 p-4 rounded-xl bg-graphite-800 text-sm text-zinc-400 border border-graphite-700">
              <Zap size={16} className="inline mr-2 text-accent" />
              <b className="text-zinc-200">Безопасность:</b> аппаратные лимиты прошиваются в команду старта. При потере связи станция сама остановит сессию по лимиту.
            </div>
          </Card>
          <div className="mt-6"><h2 className="text-xl font-semibold mb-3">Отзывы</h2>{reviews && reviews.length > 0 ? <div className="space-y-3">{reviews.map((r) => (<Card key={r.id} className="p-4"><div className="flex items-center justify-between"><div className="font-medium">{r.author ?? 'Аноним'}</div><div className="text-xs text-zinc-500">{new Date(r.created_at).toLocaleDateString('ru-RU')}</div></div><div className="mt-2 text-sm text-zinc-300">{r.text}</div></Card>))}</div> : <p className="text-sm text-zinc-400">Пока нет отзывов</p>}</div>
        </div>
        <div>
          <Card className="p-5">
            <Button className="w-full !py-3 !text-lg" onClick={() => setFlowOpen(true)}>Начать зарядку</Button>
            <p className="mt-2 text-xs text-zinc-400 text-center">Требуется авторизация</p>
            <div className="mt-4 grid grid-cols-2 gap-2">
              <Button variant="secondary" className="w-full !py-2.5" onClick={() => setSupportOpen(true)}><LifeBuoy size={15} className="mr-1 inline" />Поддержка</Button>
              <a href={`https://yandex.ru/maps?rtt=auto&rtext=${s.latitude},${s.longitude}`} target="_blank" rel="noreferrer"><Button variant="secondary" className="w-full !py-2.5"><MapPin size={15} className="mr-1 inline" />Маршрут</Button></a>
            </div>
          </Card>
        </div>
      </div>
      <StartFlowDialog open={flowOpen} onClose={() => setFlowOpen(false)} station={s} />
      <Modal open={supportOpen} onClose={() => setSupportOpen(false)} title="Поддержка" wide><p className="text-sm text-zinc-400">Напишите нам в Telegram @chargepoint_support или на support@chargepoint-road.ru</p></Modal>
    </div>
  );
}

function Stat({ title, value, accent }: { title: string; value: string; accent?: boolean }) {
  return <div><div className="text-xs text-zinc-500">{title}</div><div className={cn('text-lg font-semibold mt-1', accent ? 'text-accent' : '')}>{value}</div></div>;
}
