'use client';
import { useQuery } from '@tanstack/react-query';
import dynamic from 'next/dynamic';
import { Suspense, useEffect, useMemo, useState } from 'react';
import { Link } from 'next/link';
import { Crosshair, Navigation, Star } from 'lucide-react';
import { get, post, del } from '../../lib/api';
import { YANDEX_KEY } from '../../lib/config';
import { Badge, Button, Card, Input, Label, Skeleton, StatusBadge, cn, statusLabel } from '../../components/ui';
import type { StationDetail, StationShort } from '../../types';
import { money } from '../../lib/format';

const YaMapView = dynamic(() => import('../../components/map/YaMapView'), { ssr: false, loading: () => <Skeleton className="w-full h-full" /> });

const STATUSES = [{ k: 'free', l: 'Свободные' }, { k: 'charging', l: 'Зарядка' }, { k: 'busy', l: 'Занятые' }, { k: 'offline', l: 'Офлайн' }, { k: 'faulted', l: 'Неисправные' }];
const POWERS = [{ k: 'p3.7', l: '≤3.7' }, { k: 'p7.4', l: '≤7.4' }, { k: 'p11', l: '≤11' }, { k: 'p22', l: '≤22' }];
const VENUES = [{ k: 'hotel', l: 'Отели' }, { k: 'motel', l: 'Мотели' }, { k: 'cafe', l: 'Кафе' }, { k: 'parking', l: 'Паркинги' }, { k: 'highway', l: 'Трассы' }];

export default function MapPage() {
  const [statuses, setStatuses] = useState<string[]>([]);
  const [powers, setPowers] = useState<string[]>([]);
  const [venues, setVenues] = useState<string[]>([]);
  const [tariffMax, setTariffMax] = useState<number>(25);
  const [open24, setOpen24] = useState(false);
  const [needBooking, setNeedBooking] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [userLoc, setUserLoc] = useState<[number, number] | null>(null);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());

  const qs = useMemo(() => {
    const p = new URLSearchParams();
    statuses.forEach((s) => p.append('status', s));
    powers.forEach((pw) => p.append('power', pw));
    venues.forEach((v) => p.append('venue', v));
    if (tariffMax < 25) p.set('tariff_max', String(tariffMax));
    if (open24) p.set('open_24', 'true');
    if (needBooking) p.set('booking', 'true');
    return p.toString();
  }, [statuses, powers, venues, tariffMax, open24, needBooking]);

  const { data: stations = [], isLoading } = useQuery({
    queryKey: ['stations-map', qs],
    queryFn: () => get<StationShort[]>(`stations?${qs}`),
    refetchInterval: 30000,
  });

  const { data: selected } = useQuery({
    queryKey: ['station', selectedId],
    enabled: !!selectedId,
    queryFn: () => get<StationDetail>(`stations/${selectedId}`),
  });

  useEffect(() => {
    get<string[]>('me/favorites').then((f) => setFavorites(new Set(f))).catch(() => {});
  }, []);

  const locate = () => navigator.geolocation.getCurrentPosition((pos) => setUserLoc([pos.coords.latitude, pos.coords.longitude]), () => {}, { enableHighAccuracy: true });

  const toggleFav = async (id: string) => {
    const next = new Set(favorites);
    if (next.has(id)) { next.delete(id); await del(`me/favorites/${id}`).catch(() => {}); }
    else { next.add(id); await post(`me/favorites/${id}`).catch(() => {}); }
    setFavorites(next);
  };

  const toggle = (arr: string[], set: (v: string[]) => void) => (v: string) => set(arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v]);

  const Filters = (
    <div className="space-y-5">
      <div>
        <Label>Статус</Label>
        <div className="flex flex-wrap gap-2">
          {STATUSES.map((s) => (
            <button key={s.k} onClick={toggle(statuses, setStatuses, s.k)} className={cn('border rounded-xl px-3 py-1.5 text-xs transition-colors', statuses.includes(s.k) ? 'border-accent bg-accent/10 text-accent' : 'border-graphite-600 text-zinc-400')}>
              {s.l}
            </button>
          ))}
        </div>
      </div>
      <div>
        <Label>Мощность</Label>
        <div className="flex flex-wrap gap-2">
          {POWERS.map((p) => (
            <button key={p.k} onClick={toggle(powers, setPowers, p.k)} className={cn('border rounded-xl px-3 py-1.5 text-xs', powers.includes(p.k) ? 'border-accent bg-accent/10 text-accent' : 'border-graphite-600 text-zinc-400')}>
              {p.l}
            </button>
          ))}
        </div>
      </div>
      <div>
        <Label>Тариф до {tariffMax} ₽/кВт⋅ч</Label>
        <input type="range" min={10} max={25} step={0.5} value={tariffMax} onChange={(e) => setTariffMax(Number(e.target.value))} className="w-full accent-[#17c99e]" />
      </div>
      <div className="space-y-2 text-sm">
        <label className="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked={open24} onChange={(e) => setOpen24(e.target.checked)} className="accent-[#17c99e]" />Круглосуточно</label>
        <label className="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked={needBooking} onChange={(e) => setNeedBooking(e.target.checked)} className="accent-[#17c99e]" />С бронированием</label>
      </div>
      <div>
        <Label>Тип локации</Label>
        <div className="flex flex-wrap gap-2">
          {VENUES.map((v) => (
            <button key={v.k} onClick={toggle(venues, setVenues, v.k)} className={cn('border rounded-xl px-3 py-1.5 text-xs', venues.includes(v.k) ? 'border-accent bg-accent/10 text-accent' : 'border-graphite-600 text-zinc-400')}>
              {v.l}
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="max-w-[1600px] mx-auto px-4 py-6">
      <div className="grid lg:grid-cols-[280px_1fr_340px] gap-4 h-[calc(100vh-140px)] min-h-[520px]">
        <Card className="overflow-y-auto hidden lg:block">{Filters}</Card>
        <div className="relative rounded-2xl overflow-hidden border border-graphite-700">
          <Suspense fallback={<Skeleton className="w-full h-full" />}>
            <YaMapViewWrapper stations={stations} userLocation={userLoc} onSelect={(s) => setSelectedId(s.public_id)} />
          </Suspense>
          <Button variant="secondary" onClick={locate} className="absolute top-3 left-3 z-10 !p-3 !rounded-xl" aria-label="Моё местоположение"><Crosshair size={18} /></Button>
          {isLoading && <Skeleton className="absolute inset-0" />}
        </div>
        <div className="hidden lg:block overflow-y-auto space-y-3">
          {selected ? <StationCard station={selected} fav={favorites.has(selected.id)} onFav={() => toggleFav(selected.id)} /> : <Card className="text-sm text-zinc-400">Выберите станцию на карте</Card>}
        </div>
      </div>
      <div className="lg:hidden fixed bottom-0 inset-x-0 z-40 p-3">
        {selected ? <StationCard station={selected} fav={favorites.has(selected.id)} onFav={() => toggleFav(selected.id)} /> : null}
      </div>
    </div>
  );
}

async function YaMapViewWrapper({ stations, userLocation, onSelect }: { stations: StationShort[]; userLocation: [number, number] | null; onSelect: (s: StationShort) => void }) {
  const MapView = (await import('../../components/map/YaMapView')).default;
  return <MapView stations={stations} apiKey={YANDEX_KEY} userLocation={userLocation} onSelect={onSelect} />;
}

function StationCard({ station: s, fav, onFav }: { station: StationDetail; fav: boolean; onFav: () => void }) {
  const amenityLabels: Record<string, string> = { wc: 'Туалет', cafe: 'Кафе', wifi: 'Wi-Fi', hotel: 'Отель', parking: 'Паркинг', motel: 'Мотель' };
  return (
    <Card className="shadow-2xl">
      {s.photos[0] && <img src={s.photos[0]} alt={s.name} className="w-full h-36 object-cover rounded-xl mb-3" />}
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold leading-snug">{s.name}</h3>
          <p className="text-sm text-zinc-400">{s.address}, {s.city}</p>
        </div>
        <button onClick={onFav} aria-label="В избранное" className="p-2"><Star size={18} className={fav ? 'fill-warn text-warn' : 'text-zinc-500'} /></button>
      </div>
      <div className="mt-3"><StatusBadge status={s.status} /></div>
      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        <Badge>{s.max_power_kw} кВт</Badge>
        <Badge>Тип 2</Badge>
        <Badge className="!text-accent !border-accent/40">{money(Number(s.tariff_per_kwh))} ₽/кВт⋅ч</Badge>
        <Badge>Мин. {money(Number(s.min_launch_amount))} ₽</Badge>
      </div>
      {s.amenities.length > 0 && <p className="mt-2 text-xs text-zinc-500">{s.amenities.map((a) => amenityLabels[a] ?? a).join(', ')}</p>}
      {s.parking_info && <p className="mt-1 text-xs text-zinc-500">{s.parking_info}</p>}
      <p className="mt-1 text-xs text-zinc-500">{s.schedule?.always_open ? 'Круглосуточно' : ''}</p>
      <div className="mt-4 grid grid-cols-2 gap-2">
        <a href={`https://yandex.ru/maps?rtt=auto&rtext=${s.latitude},${s.longitude}`} target="_blank" rel="noreferrer"><Button variant="secondary" className="w-full !py-2.5 !text-sm"><Navigation size={15} className="mr-1 inline" />Маршрут</Button></a>
        <Link href={`/stations/${s.public_id}`}><Button className="w-full !py-2.5 !text-sm">Зарядиться</Button></Link>
      </div>
    </Card>
  );
}
