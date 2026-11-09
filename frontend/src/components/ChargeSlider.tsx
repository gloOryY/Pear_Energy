// src/components/ChargeSlider.tsx
"use client";

import React, { useState, useMemo } from "react";

interface CarInfo {
  id: number;
  make: string;
  model: string;
  batteryCapacity: number; // кВт·ч
  maxDcPower: number;      // кВт
}

interface ChargeSliderProps {
  car: CarInfo;
  stationPowerKw: number;
  tariffPerKwh: number;
}

export default function ChargeSlider({ car, stationPowerKw, tariffPerKwh }: ChargeSliderProps) {
  const [currentSoc, setCurrentSoc] = useState<number>(20);
  const [targetSoc, setTargetSoc] = useState<number>(80);

  // Мгновенный клиентский расчет для плавной анимации слайдера
  const calculation = useMemo(() => {
    if (targetSoc <= currentSoc) {
      return { energyKwh: 0, minutes: 0, cost: 0 };
    }

    const efficiency = 0.92;
    const socDelta = targetSoc - currentSoc;
    const grossEnergy = (car.batteryCapacity * (socDelta / 100)) / efficiency;
    const effectivePower = Math.min(stationPowerKw, car.maxDcPower);

    // Учет замедления на DC выше 80%
    let hours = 0;
    if (targetSoc > 80) {
      const e1 = (car.batteryCapacity * (Math.max(0, 80 - currentSoc) / 100)) / efficiency;
      const e2 = (car.batteryCapacity * ((targetSoc - Math.max(currentSoc, 80)) / 100)) / efficiency;
      hours = (e1 / effectivePower) + (e2 / (effectivePower * 0.45));
    } else {
      hours = grossEnergy / effectivePower;
    }

    return {
      energyKwh: Number(grossEnergy.toFixed(1)),
      minutes: Math.round(hours * 60),
      cost: Math.round(grossEnergy * tariffPerKwh),
    };
  }, [currentSoc, targetSoc, car, stationPowerKw, tariffPerKwh]);

  return (
    <div className="w-full max-w-lg p-6 bg-slate-900 border border-slate-800 rounded-2xl text-white shadow-xl">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="font-semibold text-lg">{car.make} {car.model}</h3>
          <p className="text-xs text-slate-400">Батарея: {car.batteryCapacity} кВт·ч</p>
        </div>
        <span className="px-3 py-1 bg-emerald-500/10 text-emerald-400 text-xs font-medium rounded-full border border-emerald-500/20">
          Макс. {car.maxDcPower} кВт
        </span>
      </div>

      {/* Выбор текущего уровня */}
      <div className="mb-4">
        <label className="text-sm text-slate-300 block mb-2">Текущий заряд авто:</label>
        <div className="flex items-center gap-3">
          <input
            type="number"
            min="1"
            max="95"
            value={currentSoc}
            onChange={(e) => {
              const val = Math.min(95, Math.max(0, Number(e.target.value)));
              setCurrentSoc(val);
              if (val >= targetSoc) setTargetSoc(Math.min(100, val + 10));
            }}
            className="w-20 px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-center font-bold text-white focus:outline-none focus:border-emerald-500"
          />
          <span className="text-slate-400 font-bold">%</span>
        </div>
      </div>

      {/* Слайдер целевого заряда */}
      <div className="mb-6">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-slate-300">Зарядить до:</span>
          <span className="font-bold text-emerald-400 text-base">{targetSoc}%</span>
        </div>
        <input
          type="range"
          min={currentSoc + 1}
          max={100}
          value={targetSoc}
          onChange={(e) => setTargetSoc(Number(e.target.value))}
          className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
        />
        <div className="flex justify-between text-xs text-slate-500 mt-1">
          <span>{currentSoc + 1}%</span>
          <span>80% (Оптимально)</span>
          <span>100%</span>
        </div>
      </div>

      {/* Информационные плашки */}
      <div className="grid grid-cols-3 gap-3 p-4 bg-slate-800/60 rounded-xl border border-slate-700/50">
        <div>
          <span className="text-[11px] text-slate-400 block uppercase font-medium">Энергия</span>
          <span className="text-lg font-bold text-slate-100">{calculation.energyKwh} <span className="text-xs font-normal text-slate-400">кВт·ч</span></span>
        </div>
        <div>
          <span className="text-[11px] text-slate-400 block uppercase font-medium">Время</span>
          <span className="text-lg font-bold text-slate-100">{calculation.minutes} <span className="text-xs font-normal text-slate-400">мин</span></span>
        </div>
        <div>
          <span className="text-[11px] text-slate-400 block uppercase font-medium">Стоимость</span>
          <span className="text-lg font-bold text-emerald-400">{calculation.cost} <span className="text-xs font-normal text-slate-400">₽</span></span>
        </div>
      </div>

      <button className="w-full mt-6 py-3 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-xl transition-colors shadow-lg shadow-emerald-500/10">
        Начать зарядную сессию
      </button>
    </div>
  );
}