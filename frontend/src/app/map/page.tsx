"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import YaMapView from "../../components/map/YaMapView";
import type { StationShort } from "../../types";

const RAW_API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_BASE = RAW_API.endsWith("/api/v1")
  ? RAW_API
  : `${RAW_API.replace(/\/$/, "")}/api/v1`;

export default function MapPage() {
  const [stations, setStations] = useState<StationShort[]>([]);
  const [selectedStation, setSelectedStation] = useState<StationShort | null>(null);
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [userLocation, setUserLocation] = useState<[number, number] | null>(null);
  const [loading, setLoading] = useState(true);
  const [geoMessage, setGeoMessage] = useState("");

  useEffect(() => {
    const loadStations = async () => {
      try {
        // Сначала пробуем относительный путь (если работает через nginx), иначе прямой URL бэкенда
        let res = await fetch("/api/v1/stations");
        const contentType = res.headers.get("content-type") || "";

        if (!res.ok || !contentType.includes("application/json")) {
          res = await fetch(`${API_BASE.replace(/\/$/, "")}/stations`);
        }

        if (res.ok) {
          const data = await res.json();
          const list = Array.isArray(data)
            ? data
            : Array.isArray(data?.items)
            ? data.items
            : [];
          setStations(list);
        }
      } catch {
        // Игнорируем сетевую ошибку, чтобы не вызывать оверлей Next.js
      } finally {
        setLoading(false);
      }
    };

    loadStations();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchQuery(searchInput.trim());
  };

  const handleLocateMe = () => {
    setGeoMessage("");
    if (!navigator.geolocation) {
      setGeoMessage("Геолокация не поддерживается вашим браузером");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUserLocation([pos.coords.latitude, pos.coords.longitude]);
      },
      (err) => {
        if (err.code === 1) {
          setGeoMessage("Разрешите доступ к геолокации в настройках браузера");
        } else {
          setGeoMessage("Не удалось определить местоположение");
        }
      },
      { enableHighAccuracy: false, timeout: 8000 }
    );
  };

  return (
    <div className="min-h-[calc(100vh-72px)] bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <h1 className="text-3xl font-bold text-green-400">
            Карта зарядных станций
          </h1>

          <form onSubmit={handleSearch} className="flex gap-2 w-full md:w-auto">
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Найти город или адрес..."
              className="flex-1 md:w-72 px-4 py-2.5 rounded-xl bg-gray-800 border border-gray-700 focus:border-green-400 focus:outline-none text-sm"
            />
            <button
              type="submit"
              className="px-4 py-2.5 bg-green-500 hover:bg-green-400 text-gray-900 font-semibold rounded-xl text-sm transition-colors"
            >
              Найти
            </button>
            <button
              type="button"
              onClick={handleLocateMe}
              className="px-4 py-2.5 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-200 rounded-xl text-sm transition-colors"
              title="Моё местоположение"
            >
              Геолокация
            </button>
          </form>
        </div>

        {geoMessage && (
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-sm">
            {geoMessage}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Карта OpenLayers */}
          <div className="lg:col-span-2 h-[600px] bg-gray-800 rounded-2xl border border-gray-700 p-2">
            <YaMapView
              stations={stations}
              onSelect={(s) => setSelectedStation(s)}
              searchQuery={searchQuery}
              userLocation={userLocation}
            />
          </div>

          {/* Боковая панель со списком и выбранной станцией */}
          <div className="bg-gray-800 rounded-2xl border border-gray-700 p-5 flex flex-col h-[600px]">
            {selectedStation ? (
              <div className="mb-4 p-4 rounded-xl bg-gray-900 border border-green-500/40 space-y-2">
                <div className="flex items-start justify-between">
                  <h2 className="text-lg font-bold text-green-400">
                    {selectedStation.name}
                  </h2>
                  <button
                    onClick={() => setSelectedStation(null)}
                    className="text-gray-400 hover:text-white text-sm"
                  >
                    ✕
                  </button>
                </div>
                <p className="text-sm text-gray-300">
                  {selectedStation.address || "Адрес не указан"}
                </p>
                <p className="text-xs text-gray-500">
                  Координаты: {selectedStation.latitude}, {selectedStation.longitude}
                </p>
                <div className="pt-2">
                  <Link
                    href={`/stations/${selectedStation.id}`}
                    className="inline-block w-full text-center py-2 bg-green-500 hover:bg-green-400 text-gray-900 font-semibold rounded-lg text-sm transition-colors"
                  >
                    Подробнее о станции
                  </Link>
                </div>
              </div>
            ) : null}

            <h3 className="text-base font-semibold text-gray-300 mb-3">
              Все станции ({stations.length})
            </h3>

            <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
              {loading ? (
                <p className="text-sm text-gray-400">Загрузка станций...</p>
              ) : stations.length === 0 ? (
                <p className="text-sm text-gray-400">Станции пока не добавлены.</p>
              ) : (
                stations.map((st) => (
                  <div
                    key={st.id}
                    onClick={() => setSelectedStation(st)}
                    className={`p-3.5 rounded-xl border cursor-pointer transition-colors ${
                      selectedStation?.id === st.id
                        ? "bg-gray-900 border-green-500"
                        : "bg-gray-900/60 border-gray-700 hover:border-gray-500"
                    }`}
                  >
                    <div className="font-semibold text-sm text-white">
                      {st.name}
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      {st.address || `${st.latitude}, ${st.longitude}`}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}