"use client";

import React, { useState } from "react";

const CONNECTOR_OPTIONS = [
  { label: "Type 2", value: "type2" },
  { label: "CCS 2", value: "ccs2" },
  { label: "CHAdeMO", value: "chademo" },
  { label: "GB/T (DC)", value: "gbt_dc" },
  { label: "GB/T (AC)", value: "gbt_ac" },
];

interface ConnectorItem {
  id?: string;
  connector_number: number;
  type: string;
  max_power_kw: number;
  status: string;
}

export default function StationForm({ initialData, onSubmit }: { initialData?: any; onSubmit: (data: any) => void }) {
  const [name, setName] = useState(initialData?.name || "");
  const [publicId, setPublicId] = useState(initialData?.public_id || "");
  const [serialNumber, setSerialNumber] = useState(initialData?.serial_number || "");
  const [locationId, setLocationId] = useState(initialData?.location_id || "");
  const [deviceToken, setDeviceToken] = useState(initialData?.device_token || "dev-token-secret");
  const [maxPowerKw, setMaxPowerKw] = useState(initialData?.max_power_kw || 22.0);
  const [imageUrl, setImageUrl] = useState(initialData?.image_url || "");
  const [lat, setLat] = useState(initialData?.latitude || 55.751244);
  const [lon, setLon] = useState(initialData?.longitude || 37.618423);

  // Тарифные ставки
  const [tariffStart, setTariffStart] = useState(initialData?.tariff_start || 0.0);
  const [tariffPerMinute, setTariffPerMinute] = useState(initialData?.tariff_per_minute || 0.0);
  const [tariffPerKwh, setTariffPerKwh] = useState(initialData?.tariff_per_kwh || 15.0);
  const [tariffPerMinuteIdle, setTariffPerMinuteIdle] = useState(initialData?.tariff_per_minute_idle || 5.0);
  const [minLaunchAmount, setMinLaunchAmount] = useState(initialData?.min_launch_amount || 100.0);

  // Разъёмы станции
  const [connectors, setConnectors] = useState<ConnectorItem[]>(
    initialData?.connectors?.length
      ? initialData.connectors
      : [{ connector_number: 1, type: "type2", max_power_kw: 22.0, status: "available" }]
  );

  const addConnector = () => {
    setConnectors([
      ...connectors,
      {
        connector_number: connectors.length + 1,
        type: "ccs2",
        max_power_kw: maxPowerKw,
        status: "available",
      },
    ]);
  };

  const removeConnector = (index: number) => {
    setConnectors(connectors.filter((_, idx) => idx !== index));
  };

  const updateConnector = (index: number, field: keyof ConnectorItem, value: any) => {
    const updated = [...connectors];
    updated[index] = { ...updated[index], [field]: value };
    setConnectors(updated);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (initialData?.id) {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`/api/v1/stations/${initialData.id}/photo`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setImageUrl(data.image_url);
    } else {
      // Для новой станции можно временно сгенерировать data URL или сохранить файл отдельно
      const reader = new FileReader();
      reader.onload = () => setImageUrl(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      name,
      public_id: publicId,
      serial_number: serialNumber,
      location_id: locationId,
      device_token: deviceToken,
      max_power_kw: Number(maxPowerKw),
      latitude: Number(lat),
      longitude: Number(lon),
      image_url: imageUrl,
      tariff_start: Number(tariffStart),
      tariff_per_minute: Number(tariffPerMinute),
      tariff_per_kwh: Number(tariffPerKwh),
      tariff_per_minute_idle: Number(tariffPerMinuteIdle),
      min_launch_amount: Number(minLaunchAmount),
      connectors,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl bg-white p-6 rounded-xl border border-gray-200">
      <h2 className="text-lg font-semibold text-gray-800">Параметры зарядной станции</h2>

      {/* Основная информация */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-700">Название</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 w-full border rounded-md p-2 text-sm"
            required
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700">Публичный ID (QR-код)</label>
          <input
            type="text"
            value={publicId}
            onChange={(e) => setPublicId(e.target.value)}
            className="mt-1 w-full border rounded-md p-2 text-sm"
            required
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700">Серийный номер</label>
          <input
            type="text"
            value={serialNumber}
            onChange={(e) => setSerialNumber(e.target.value)}
            className="mt-1 w-full border rounded-md p-2 text-sm"
            required
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700">Общая мощность (кВт)</label>
          <input
            type="number"
            step="0.1"
            value={maxPowerKw}
            onChange={(e) => setMaxPowerKw(parseFloat(e.target.value))}
            className="mt-1 w-full border rounded-md p-2 text-sm"
            required
          />
        </div>
      </div>

      {/* Фотография зарядки */}
      <div className="pt-2 border-t">
        <label className="block text-xs font-medium text-gray-700 mb-1">Фотография станции</label>
        <input type="file" accept="image/*" onChange={handleFileUpload} className="text-sm text-gray-500" />
        {imageUrl && (
          <img src={imageUrl} alt="Станция" className="mt-2 h-32 w-48 object-cover rounded-lg border" />
        )}
      </div>

      {/* Поддерживаемые разъёмы */}
      <div className="pt-2 border-t">
        <div className="flex justify-between items-center mb-2">
          <label className="text-sm font-medium text-gray-800">Разъёмы (порты)</label>
          <button
            type="button"
            onClick={addConnector}
            className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 py-1 px-3 rounded-md border"
          >
            + Добавить разъём
          </button>
        </div>

        <div className="space-y-2">
          {connectors.map((c, idx) => (
            <div key={idx} className="flex items-center gap-3 p-2 bg-gray-50 rounded-lg border text-sm">
              <span className="text-xs font-bold text-gray-500 w-6">#{idx + 1}</span>
              <select
                value={c.type}
                onChange={(e) => updateConnector(idx, "type", e.target.value)}
                className="border rounded p-1 text-sm bg-white"
              >
                {CONNECTOR_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
              <div className="flex items-center gap-1">
                <input
                  type="number"
                  step="0.1"
                  value={c.max_power_kw}
                  onChange={(e) => updateConnector(idx, "max_power_kw", parseFloat(e.target.value))}
                  className="w-20 border rounded p-1 text-sm bg-white"
                />
                <span className="text-xs text-gray-500">кВт</span>
              </div>
              {connectors.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeConnector(idx)}
                  className="ml-auto text-xs text-red-600 hover:underline"
                >
                  Удалить
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Тарификация */}
      <div className="pt-2 border-t">
        <label className="block text-sm font-medium text-gray-800 mb-2">Настройка тарифа</label>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 bg-blue-50/50 rounded-lg border border-blue-100">
            <label className="block text-xs font-semibold text-blue-900">Старт зарядки (фикс)</label>
            <input
              type="number"
              step="0.01"
              value={tariffStart}
              onChange={(e) => setTariffStart(parseFloat(e.target.value))}
              className="mt-1 w-full border rounded p-1.5 text-sm bg-white"
              placeholder="0.00 ₽"
            />
          </div>
          <div className="p-3 bg-blue-50/50 rounded-lg border border-blue-100">
            <label className="block text-xs font-semibold text-blue-900">Поминутная оплата</label>
            <input
              type="number"
              step="0.01"
              value={tariffPerMinute}
              onChange={(e) => setTariffPerMinute(parseFloat(e.target.value))}
              className="mt-1 w-full border rounded p-1.5 text-sm bg-white"
              placeholder="0.00 ₽/мин"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-600">Стоимость за кВт·ч (₽)</label>
            <input
              type="number"
              step="0.01"
              value={tariffPerKwh}
              onChange={(e) => setTariffPerKwh(parseFloat(e.target.value))}
              className="mt-1 w-full border rounded p-1.5 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-600">Мин. баланс для старта (₽)</label>
            <input
              type="number"
              step="0.01"
              value={minLaunchAmount}
              onChange={(e) => setMinLaunchAmount(parseFloat(e.target.value))}
              className="mt-1 w-full border rounded p-1.5 text-sm"
            />
          </div>
        </div>
      </div>

      <button
        type="submit"
        className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 rounded-lg transition"
      >
        Сохранить станцию
      </button>
    </form>
  );
}