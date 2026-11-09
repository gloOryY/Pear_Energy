# backend/app/services/charging_calc.py
from dataclasses import dataclass

@dataclass
class ChargingEstimate:
    energy_needed_kwh: float
    duration_minutes: int
    total_cost_rub: float
    effective_power_kw: float

def calculate_charge_estimate(
    battery_capacity_kwh: float,
    current_soc: int,
    target_soc: int,
    station_power_kw: float,
    station_type: str,          # "AC" или "DC"
    car_max_ac_kw: float,
    car_max_dc_kw: float,
    price_per_kwh: float,
    efficiency: float = 0.92
) -> ChargingEstimate:
    if target_soc <= current_soc:
        return ChargingEstimate(0.0, 0, 0.0, 0.0)

    # 1. Полезная энергия, которую необходимо залить в ячейки
    soc_delta_percent = target_soc - current_soc
    net_energy_kwh = battery_capacity_kwh * (soc_delta_percent / 100.0)
    
    # 2. Общая энергия от сети с учетом тепловых потерь и КПД
    gross_energy_kwh = net_energy_kwh / efficiency

    # 3. Лимитирующая мощность (слабое звено)
    car_power_limit = car_max_dc_kw if station_type.upper() == "DC" else car_max_ac_kw
    effective_power_kw = min(station_power_kw, car_power_limit)

    # 4. Расчет времени с учетом замедления после 80% на DC
    if station_type.upper() == "DC" and target_soc > 80:
        # Разбиваем на отрезок до 80% и отрезок 80-100% (с понижением мощности в ~2 раза)
        soc_up_to_80 = max(0, min(target_soc, 80) - current_soc)
        soc_above_80 = target_soc - max(current_soc, 80)

        e1 = (battery_capacity_kwh * (soc_up_to_80 / 100.0)) / efficiency
        e2 = (battery_capacity_kwh * (soc_above_80 / 100.0)) / efficiency

        time_hours = (e1 / effective_power_kw) + (e2 / (effective_power_kw * 0.45))
    else:
        time_hours = gross_energy_kwh / effective_power_kw

    duration_minutes = int(round(time_hours * 60))
    total_cost_rub = round(gross_energy_kwh * price_per_kwh, 2)

    return ChargingEstimate(
        energy_needed_kwh=round(gross_energy_kwh, 2),
        duration_minutes=duration_minutes,
        total_cost_rub=total_cost_rub,
        effective_power_kw=effective_power_kw
    )