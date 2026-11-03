"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface Connector {
  id?: string;
  connector_number: number;
  type: string;
  max_power_kw: number;
  status: string;
}

interface Station {
  id: string;
  name: string;
  address?: string;
  city?: string;
  latitude: number;
  longitude: number;
  status: string;
  max_power_kw?: number;
  image_url?: string | null;
  tariff_start: number;
  tariff_per_minute: number;
  connector_type?: string;
  connectors?: Connector[];
}

const CONNECTOR_BUTTONS = [
  { id: "all", label: "Все станции" },
  { id: "schuko", label: "🔌 Розетка 220V (Schuko)" },
  { id: "type2", label: "Type 2 (AC)" },
  { id: "ccs2", label: "CCS 2 (DC)" },
  { id: "gbt_dc", label: "GB/T (DC)" },
  { id: "gbt_ac", label: "GB/T (AC)" },
  { id: "chademo", label: "CHAdeMO" },
];

const CONNECTOR_LABELS: Record<string, string> = {
  schuko: "Евророзетка 220V (Schuko)",
  type2: "Type 2 (AC)",
  ccs2: "CCS 2 (DC)",
  gbt_dc: "GB/T (DC)",
  gbt_ac: "GB/T (AC)",
  chademo: "CHAdeMO",
};

async function apiFetch(path: string): Promise<Response> {
  try {
    const res = await fetch(`/api/v1${path}`);
    if (res.status !== 404 && res.status !== 502) return res;
  } catch {}

  const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
  return fetch(`http://${host}:8000/api/v1${path}`);
}

export default function HomePage() {
  const [stations, setStations] = useState<Station[]>([]);
  const [search, setSearch] = useState("");
  const [selectedFilter, setSelectedFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStations() {
      try {
        const res = await apiFetch("/stations");
        if (res.ok) {
          const data = await res.json();
          setStations(Array.isArray(data) ? data : data?.items || []);
        }
      } catch (err) {
        console.error("Ошибка загрузки станций", err);
      } finally {
        setLoading(false);
      }
    }
    loadStations();
  }, []);

  // Точная проверка наличия нужного коннектора
  const matchesConnector = (st: Station, filterId: string) => {
    if (filterId === "all") return true;

    const target = filterId.toLowerCase();

    // 1. Проверка по массиву connectors
    if (Array.isArray(st.connectors) && st.connectors.length > 0) {
      const found = st.connectors.some((c: any) => {
        const typeStr = (c.type || c.connector_type || "").toLowerCase();
        return typeStr === target;
      });
      if (found) return true;
    }

    // 2. Проверка по одиночному connector_type
    if (st.connector_type && st.connector_type.toLowerCase() === target) {
      return true;
    }

    return false;
  };

  const filteredStations = stations.filter((st) => {
    const matchesSearch =
      st.name.toLowerCase().includes(search.toLowerCase()) ||
      (st.address && st.address.toLowerCase().includes(search.toLowerCase()));

    const matchesType = matchesConnector(st, selectedFilter);

    return matchesSearch && matchesType;
  });

  return (
    <div className="min-h-screen bg-gray-950 text-white selection:bg-green-500 selection:text-gray-950">
      <section className="relative border-b border-gray-800 bg-gradient-to-b from-gray-900 via-gray-900/50 to-gray-950 px-6 py-16 text-center">
        <div className="mx-auto max-w-4xl space-y-4">
          <span className="inline-block rounded-full bg-green-500/10 px-4 py-1.5 text-xs font-semibold text-green-400 border border-green-500/20">
            Сеть зарядных станций нового поколения
          </span>
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">
            Заряжайте электромобиль <span className="text-green-400">просто и выгодно</span>
          </h1>
          <p className="mx-auto max-w-2xl text-base text-gray-400">
            Подключение через Type 2, быстрые порты DC или стандартную евророзетку 220V для вашего штатного зарядного кабеля. Прозрачная поминутная тарификация без переплат.
          </p>

          <div className="mx-auto mt-8 max-w-3xl space-y-4">
            <input
              type="text"
              placeholder="Поиск по адресу или названию станции..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-2xl border border-gray-700 bg-gray-900/80 px-5 py-3.5 text-sm placeholder-gray-500 focus:border-green-400 focus:outline-none focus:ring-1 focus:ring-green-400 backdrop-blur"
            />

            <div className="flex flex-wrap justify-center gap-2 pt-2">
              {CONNECTOR_BUTTONS.map((btn) => (
                <button
                  key={btn.id}
                  onClick={() => setSelectedFilter(btn.id)}
                  className={`rounded-xl px-3.5 py-1.5 text-xs font-medium transition-all ${
                    selectedFilter === btn.id
                      ? "bg-green-500 text-gray-950 shadow-md font-semibold scale-105"
                      : "bg-gray-900 text-gray-400 hover:text-white border border-gray-800 hover:border-gray-700"
                  }`}
                >
                  {btn.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-12">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-xl font-bold tracking-tight text-white">
            Доступные станции ({filteredStations.length})
          </h2>
          <Link
            href="/map"
            className="text-xs font-semibold text-green-400 hover:text-green-300 transition-colors"
          >
            Открыть интерактивную карту →
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((n) => (
              <div key={n} className="h-72 rounded-2xl bg-gray-900 animate-pulse border border-gray-800" />
            ))}
          </div>
        ) : filteredStations.length === 0 ? (
          <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-12 text-center text-gray-400">
            Станций с выбранным разъёмом не найдено.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredStations.map((st) => (
              <div
                key={st.id}
                className="group flex flex-col justify-between overflow-hidden rounded-2xl border border-gray-800 bg-gray-900/60 hover:border-gray-700 transition-all hover:shadow-xl hover:shadow-green-500/5"
              >
                <div className="relative h-44 w-full bg-gray-800">
                  {st.image_url ? (
                    <img
                      src={st.image_url}
                      alt={st.name}
                      className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                    />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center bg-gray-800 text-xs text-gray-500">
                      Фотография отсутствует
                    </div>
                  )}
                  <div className="absolute top-3 right-3 rounded-lg bg-gray-950/80 backdrop-blur px-2.5 py-1 text-xs font-bold text-green-400 border border-gray-700">
                    {st.max_power_kw || 22} кВт
                  </div>
                </div>

                <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                  <div className="space-y-1">
                    <h3 className="font-bold text-base text-white group-hover:text-green-400 transition-colors">
                      {st.name}
                    </h3>
                    <p className="text-xs text-gray-400 line-clamp-2">
                      {st.address || "Адрес не указан"}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider block">
                      Поддерживаемые разъёмы:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {st.connectors && st.connectors.length > 0 ? (
                        st.connectors.map((c) => (
                          <span
                            key={c.id || c.connector_number}
                            className={`rounded-lg px-2.5 py-1 text-[11px] font-medium border ${
                              c.type === "schuko"
                                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400 font-semibold"
                                : "bg-gray-800 border-gray-700 text-gray-300"
                            }`}
                          >
                            {CONNECTOR_LABELS[c.type] || c.type}
                          </span>
                        ))
                      ) : (
                        <span className="rounded-lg px-2.5 py-1 text-[11px] font-medium border bg-gray-800 border-gray-700 text-gray-300">
                          {CONNECTOR_LABELS[st.connector_type || ""] || st.connector_type || "Не указан"}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="rounded-xl bg-gray-950/60 p-3 border border-gray-800/80">
                    <div className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider">
                      Тариф
                    </div>
                    <div className="mt-1 flex items-baseline justify-between text-sm">
                      <span className="text-gray-300">
                        Старт: <strong className="text-white">{st.tariff_start || 0} ₽</strong>
                      </span>
                      <span className="text-green-400 font-semibold">
                        {st.tariff_per_minute || 0} ₽ / мин
                      </span>
                    </div>
                  </div>

                  <Link
                    href={`/stations/${st.id}`}
                    className="block w-full text-center rounded-xl bg-green-500 py-2.5 text-xs font-bold text-gray-950 hover:bg-green-400 transition-colors"
                  >
                    Перейти к зарядке
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}