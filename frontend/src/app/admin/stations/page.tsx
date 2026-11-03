"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

import "ol/ol.css";
import Map from "ol/Map";
import View from "ol/View";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import OSM from "ol/source/OSM";
import VectorSource from "ol/source/Vector";
import Feature from "ol/Feature";
import Point from "ol/geom/Point";
import { fromLonLat, toLonLat } from "ol/proj";
import { Style, Circle as CircleStyle, Fill, Stroke, Text } from "ol/style";

const CONNECTOR_OPTIONS = [
  { label: "Евророзетка 220V (Schuko)", value: "schuko", defaultKw: 3.5 },
  { label: "Type 2 (AC)", value: "type2", defaultKw: 22.0 },
  { label: "CCS 2 (DC)", value: "ccs2", defaultKw: 60.0 },
  { label: "GB/T (DC)", value: "gbt_dc", defaultKw: 60.0 },
  { label: "GB/T (AC)", value: "gbt_ac", defaultKw: 7.0 },
  { label: "CHAdeMO", value: "chademo", defaultKw: 50.0 },
];

async function apiFetch(path: string, options?: RequestInit): Promise<Response> {
  try {
    const res = await fetch(`/api/v1${path}`, options);
    if (res.status !== 404 && res.status !== 502) {
      return res;
    }
  } catch {}

  const host = typeof window !== "undefined" ? window.location.hostname : "localhost";
  return fetch(`http://${host}:8000/api/v1${path}`, options);
}

export default function AdminStationsPage() {
  const router = useRouter();

  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef(null);
  const stationsSourceRef = useRef<VectorSource>(new VectorSource());
  const selectedPointSourceRef = useRef<VectorSource>(new VectorSource());

  const [isMounted, setIsMounted] = useState(false);
  const [stations, setStations] = useState<any[]>([]);

  const [name, setName] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [address, setAddress] = useState("");

  const [imageUrl, setImageUrl] = useState("");
  const [isUploadingPhoto, setIsUploadingPhoto] = useState(false);

  const [maxPowerKw, setMaxPowerKw] = useState("22");
  const [selectedConnectors, setSelectedConnectors] = useState<string[]>(["schuko", "type2"]);

  const [tariffStart, setTariffStart] = useState("50");
  const [tariffPerMinute, setTariffPerMinute] = useState("3");

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);

  const [message, setMessage] = useState({ text: "", type: "" });
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    const email = localStorage.getItem("userEmail");
    if (email !== "admin@example.com") {
      router.push("/");
    } else {
      fetchStations();
    }
  }, [router]);

  const fetchStations = async () => {
    try {
      const res = await apiFetch("/stations");
      if (res.ok) {
        const data = await res.json();
        setStations(Array.isArray(data) ? data : data?.items || []);
      }
    } catch {}
  };

  const toggleConnector = (connType: string) => {
    setSelectedConnectors((prev) =>
      prev.includes(connType)
        ? prev.length > 1
          ? prev.filter((c) => c !== connType)
          : prev
        : [...prev, connType]
    );
  };

  const handlePhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploadingPhoto(true);
    setMessage({ text: "", type: "" });

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await apiFetch("/stations/upload-photo", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error("Не удалось загрузить фото");
      }

      const data = await res.json();
      setImageUrl(data.image_url);
      setMessage({ text: "Фото успешно загружено!", type: "success" });
    } catch (err: any) {
      setMessage({ text: err.message || "Ошибка загрузки файла", type: "error" });
    } finally {
      setIsUploadingPhoto(false);
    }
  };

  useEffect(() => {
    if (!isMounted || !mapContainerRef.current || mapInstanceRef.current) return;

    const stationsLayer = new VectorLayer({
      source: stationsSourceRef.current,
      style: (feature) =>
        new Style({
          image: new CircleStyle({
            radius: 8,
            fill: new Fill({ color: "#22c55e" }),
            stroke: new Stroke({ color: "#ffffff", width: 2 }),
          }),
          text: new Text({
            text: feature.get("name") || "",
            offsetY: -16,
            font: "bold 12px sans-serif",
            fill: new Fill({ color: "#ffffff" }),
            stroke: new Stroke({ color: "#111827", width: 3 }),
          }),
        }),
    });

    const selectedPointLayer = new VectorLayer({
      source: selectedPointSourceRef.current,
      style: new Style({
        image: new CircleStyle({
          radius: 10,
          fill: new Fill({ color: "#ef4444" }),
          stroke: new Stroke({ color: "#ffffff", width: 2.5 }),
        }),
      }),
    });

    const map = new Map({
      target: mapContainerRef.current,
      layers: [
        new TileLayer({ source: new OSM() }),
        stationsLayer,
        selectedPointLayer,
      ],
      view: new View({
        center: fromLonLat([37.6176, 55.7558]),
        zoom: 10,
      }),
    });

    map.on("singleclick", async (event) => {
      const [lon, lat] = toLonLat(event.coordinate);
      const latStr = lat.toFixed(6);
      const lonStr = lon.toFixed(6);

      setLatitude(latStr);
      setLongitude(lonStr);
      setAddress("Определение адреса...");
      setShowDropdown(false);

      try {
        const res = await fetch(
          `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latStr}&lon=${lonStr}&accept-language=ru`
        );
        if (res.ok) {
          const data = await res.json();
          setAddress(data?.display_name || "Точный адрес не найден");
        } else {
          setAddress("Точный адрес не найден");
        }
      } catch {
        setAddress("Не удалось определить адрес автоматически");
      }
    });

    mapInstanceRef.current = map;

    return () => {
      map.setTarget(undefined);
      mapInstanceRef.current = null;
    };
  }, [isMounted]);

  useEffect(() => {
    const source = stationsSourceRef.current;
    source.clear();

    stations.forEach((st) => {
      const lat = parseFloat(st.latitude);
      const lon = parseFloat(st.longitude);
      if (!isNaN(lat) && !isNaN(lon)) {
        const feature = new Feature({
          geometry: new Point(fromLonLat([lon, lat])),
          name: st.name,
        });
        source.addFeature(feature);
      }
    });
  }, [stations, isMounted]);

  useEffect(() => {
    const source = selectedPointSourceRef.current;
    source.clear();

    const lat = parseFloat(latitude.replace(",", "."));
    const lon = parseFloat(longitude.replace(",", "."));

    if (!isNaN(lat) && !isNaN(lon)) {
      const feature = new Feature({
        geometry: new Point(fromLonLat([lon, lat])),
      });
      source.addFeature(feature);
    }
  }, [latitude, longitude, isMounted]);

  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      if (searchQuery.length > 2) {
        try {
          const res = await fetch(
            `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
              searchQuery
            )}&limit=5&accept-language=ru`
          );
          if (res.ok) {
            const data = await res.json();
            setSearchResults(Array.isArray(data) ? data : []);
            setShowDropdown(true);
          }
        } catch {}
      } else {
        setSearchResults([]);
        setShowDropdown(false);
      }
    }, 600);

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery]);

  const handleSelectSuggestion = (place: any) => {
    const latNum = parseFloat(place.lat);
    const lonNum = parseFloat(place.lon);
    const lat = latNum.toFixed(6);
    const lon = lonNum.toFixed(6);

    if (mapInstanceRef.current) {
      mapInstanceRef.current.getView().animate({
        center: fromLonLat([lonNum, latNum]),
        zoom: 15,
        duration: 500,
      });
    }

    setLatitude(lat);
    setLongitude(lon);
    setAddress(place.display_name);
    setShowDropdown(false);
    setSearchQuery("");
  };

  const handleAddStation = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage({ text: "", type: "" });

    const latNum = parseFloat(latitude.replace(",", "."));
    const lonNum = parseFloat(longitude.replace(",", "."));
    const totalPower = parseFloat(maxPowerKw) || 22.0;

    const newStation = {
      name,
      latitude: latNum,
      longitude: lonNum,
      address,
      city: address.split(",")[0]?.trim() || "Рязань",
      status: "available",
      max_power_kw: totalPower,
      image_url: imageUrl || null,
      tariff_start: parseFloat(tariffStart) || 0.0,
      tariff_per_minute: parseFloat(tariffPerMinute) || 0.0,
      tariff_per_kwh: 0.0,
      connectors: selectedConnectors.map((cType, idx) => {
        const option = CONNECTOR_OPTIONS.find((o) => o.value === cType);
        return {
          connector_number: idx + 1,
          type: cType,
          max_power_kw: Math.min(totalPower, option?.defaultKw || totalPower),
          status: "available",
        };
      }),
    };

    try {
      const res = await apiFetch("/stations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newStation),
      });

      if (!res.ok) {
        let errorDetail = `HTTP ${res.status}`;
        try {
          const errData = await res.json();
          errorDetail = typeof errData.detail === "string" ? errData.detail : JSON.stringify(errData.detail);
        } catch {}
        throw new Error(`Ошибка при сохранении (${errorDetail})`);
      }

      setMessage({ text: "Станция успешно добавлена!", type: "success" });
      setName("");
      setLatitude("");
      setLongitude("");
      setAddress("");
      setImageUrl("");
      setSearchQuery("");
      fetchStations();
    } catch (err: any) {
      setMessage({ text: err.message, type: "error" });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteStation = async (id: string | number) => {
    if (!confirm("Удалить станцию?")) return;
    setMessage({ text: "", type: "" });

    try {
      const res = await apiFetch(`/stations/${id}`, { method: "DELETE" });
      if (!res.ok && res.status !== 204) {
        throw new Error("Не удалось удалить станцию");
      }
      setStations((prev) => prev.filter((s) => s.id !== id));
      setMessage({ text: "Станция удалена!", type: "success" });
    } catch (err: any) {
      setMessage({ text: err.message, type: "error" });
    }
  };

  if (!isMounted) {
    return <div suppressHydrationWarning className="min-h-[calc(100vh-72px)] bg-gray-900 p-8 text-white" />;
  }

  return (
    <div suppressHydrationWarning className="min-h-[calc(100vh-72px)] bg-gray-900 p-8 text-white">
      <div className="max-w-6xl mx-auto space-y-8">
        <h1 className="text-3xl font-bold text-green-400">Управление зарядными станциями</h1>

        {message.text && (
          <div
            className={`p-4 rounded-xl border ${
              message.type === "success"
                ? "bg-green-500/10 border-green-500/30 text-green-400"
                : "bg-red-500/10 border-red-500/30 text-red-400"
            }`}
          >
            {message.text}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-gray-800 p-6 rounded-2xl border border-gray-700 space-y-5">
            <h2 className="text-xl font-semibold">Добавить новую станцию</h2>

            <div className="relative">
              <label className="block text-sm text-gray-400 mb-1">Поиск места на карте (OpenStreetMap)</label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Начните вводить адрес или объект..."
                className="w-full p-3 rounded-xl bg-gray-900 border border-gray-600 focus:border-green-400 focus:outline-none"
              />
              {showDropdown && searchResults.length > 0 && (
                <ul className="absolute z-20 w-full mt-1 bg-gray-800 border border-gray-600 rounded-xl shadow-xl max-h-60 overflow-y-auto">
                  {searchResults.map((place: any) => (
                    <li
                      key={place.place_id}
                      onClick={() => handleSelectSuggestion(place)}
                      className="p-3 hover:bg-gray-700 cursor-pointer text-sm border-b border-gray-700 last:border-none"
                    >
                      {place.display_name}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <form onSubmit={handleAddStation} className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-1">Название станции</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  placeholder="Например: ЭЗС Улица Павлова (с розеткой)"
                  className="w-full p-3 rounded-xl bg-gray-900 border border-gray-600 focus:border-green-400 focus:outline-none"
                />
              </div>

              {/* Загрузка фото как файл с компьютера */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">Фотография станции</label>
                <div className="flex items-center gap-4">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handlePhotoUpload}
                    disabled={isUploadingPhoto}
                    className="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-gray-700 file:text-green-400 hover:file:bg-gray-600 cursor-pointer"
                  />
                  {isUploadingPhoto && <span className="text-xs text-yellow-400 animate-pulse">Загрузка...</span>}
                </div>
                {imageUrl && (
                  <div className="mt-3 relative inline-block">
                    <img
                      src={imageUrl}
                      alt="Превью"
                      className="h-28 w-44 object-cover rounded-xl border border-gray-600 shadow-md"
                    />
                    <button
                      type="button"
                      onClick={() => setImageUrl("")}
                      className="absolute -top-2 -right-2 bg-red-600 hover:bg-red-700 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs"
                    >
                      ×
                    </button>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Общая мощность станции (кВт)</label>
                <input
                  type="number"
                  step="0.1"
                  value={maxPowerKw}
                  onChange={(e) => setMaxPowerKw(e.target.value)}
                  required
                  placeholder="Например: 22.0 или 3.5 для розетки"
                  className="w-full p-3 rounded-xl bg-gray-900 border border-gray-600 focus:border-green-400 focus:outline-none"
                />
              </div>

              {/* Мультивыбор разъёмов, включая Schuko */}
              <div>
                <label className="block text-sm text-gray-400 mb-2">
                  Поддерживаемые разъёмы / выходы (выберите доступные)
                </label>
                <div className="flex flex-wrap gap-2">
                  {CONNECTOR_OPTIONS.map((c) => {
                    const active = selectedConnectors.includes(c.value);
                    return (
                      <button
                        type="button"
                        key={c.value}
                        onClick={() => toggleConnector(c.value)}
                        className={`px-3 py-2 rounded-xl text-xs font-semibold border transition-all ${
                          active
                            ? "bg-green-500 text-gray-900 border-green-400 shadow-md"
                            : "bg-gray-900 text-gray-300 border-gray-600 hover:border-gray-400"
                        }`}
                      >
                        {c.label} {active ? "✓" : "+"}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Тариф: ТОЛЬКО старт и поминутно */}
              <div className="p-4 rounded-xl bg-gray-900 border border-gray-700 space-y-3">
                <span className="text-xs font-semibold text-green-400 uppercase tracking-wider block">
                  Тарификация сессии (без кВт·ч)
                </span>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Старт зарядки (₽ фикс)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={tariffStart}
                      onChange={(e) => setTariffStart(e.target.value)}
                      required
                      placeholder="0.00"
                      className="w-full p-2.5 rounded-lg bg-gray-800 border border-gray-600 text-sm focus:border-green-400 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Поминутная оплата (₽/мин)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={tariffPerMinute}
                      onChange={(e) => setTariffPerMinute(e.target.value)}
                      required
                      placeholder="0.00"
                      className="w-full p-2.5 rounded-lg bg-gray-800 border border-gray-600 text-sm focus:border-green-400 focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Широта (Latitude)</label>
                  <input
                    type="text"
                    value={latitude}
                    onChange={(e) => setLatitude(e.target.value)}
                    required
                    placeholder="55.755800"
                    className="w-full p-3 rounded-xl bg-gray-900 border border-gray-600 focus:border-green-400 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm text-gray-400 mb-1">Долгота (Longitude)</label>
                  <input
                    type="text"
                    value={longitude}
                    onChange={(e) => setLongitude(e.target.value)}
                    required
                    placeholder="37.617600"
                    className="w-full p-3 rounded-xl bg-gray-900 border border-gray-600 focus:border-green-400 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1">Адрес (кликните по карте)</label>
                <input
                  type="text"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  required
                  className="w-full p-3 rounded-xl bg-gray-900 border border-gray-600 focus:border-green-400 focus:outline-none"
                />
              </div>

              <button
                type="submit"
                disabled={isLoading || isUploadingPhoto}
                className="w-full py-3 bg-green-500 hover:bg-green-400 text-gray-900 font-bold rounded-xl transition-colors disabled:opacity-50"
              >
                {isLoading ? "Сохранение..." : "Добавить станцию"}
              </button>
            </form>
          </div>

          <div className="bg-gray-800 p-4 rounded-2xl border border-gray-700 flex flex-col">
            <p className="text-sm text-gray-400 mb-3">
              Кликните на карту для определения адреса и координат:
            </p>
            <div ref={mapContainerRef} className="w-full h-[520px] rounded-xl overflow-hidden border border-gray-700" />
          </div>
        </div>

        <div className="bg-gray-800 p-6 rounded-2xl border border-gray-700">
          <h2 className="text-xl font-semibold mb-4">Список станций ({stations.length})</h2>
          <div className="space-y-4">
            {stations.map((st) => (
              <div
                key={st.id}
                className="flex flex-col md:flex-row md:items-center justify-between p-4 bg-gray-900 rounded-xl border border-gray-700 gap-4"
              >
                <div className="flex items-center gap-4">
                  {st.image_url ? (
                    <img
                      src={st.image_url}
                      alt={st.name}
                      className="h-16 w-24 object-cover rounded-lg border border-gray-700 flex-shrink-0"
                    />
                  ) : (
                    <div className="h-16 w-24 bg-gray-800 border border-gray-700 rounded-lg flex items-center justify-center text-xs text-gray-500 flex-shrink-0">
                      Нет фото
                    </div>
                  )}

                  <div className="space-y-1">
                    <div className="font-bold text-white text-base">{st.name}</div>
                    <div className="text-xs text-gray-400">
                      {st.address || "Адрес не указан"} ({st.latitude}, {st.longitude})
                    </div>

                    <div className="flex flex-wrap items-center gap-2 pt-1">
                      <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs font-semibold">
                        {st.max_power_kw} кВт
                      </span>
                      {st.connectors?.map((conn: any) => (
                        <span
                          key={conn.id || conn.connector_number}
                          className="px-2 py-0.5 bg-gray-800 text-gray-300 border border-gray-700 rounded text-xs"
                        >
                          {conn.type === "schuko" ? "Розетка 220В" : conn.type}
                        </span>
                      ))}
                      <span className="text-xs text-green-400 font-medium">
                        Старт: {st.tariff_start || 0} ₽ | Минута: {st.tariff_per_minute || 0} ₽
                      </span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => handleDeleteStation(st.id)}
                  className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg text-sm transition-colors self-end md:self-center"
                >
                  Удалить
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
