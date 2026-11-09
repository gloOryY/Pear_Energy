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
    car_max_ac_kw: float = 11.0,
    car_max_dc_kw: float = 120.0,
    price_per_kwh: float = 0.0,
    price_per_minute: float = 0.0,
    price_start: float = 0.0,
    efficiency: float = 0.92,
) -> ChargingEstimate:
    if target_soc <= current_soc or battery_capacity_kwh <= 0:
        return ChargingEstimate(0.0, 0, 0.0, 0.0)

    # 1. Полезная энергия, которую необходимо залить в батарею
    soc_delta_percent = target_soc - current_soc
    net_energy_kwh = battery_capacity_kwh * (soc_delta_percent / 100.0)

    # 2. Общая энергия от сети с учетом тепловых потерь и КПД (~92%)
    gross_energy_kwh = net_energy_kwh / efficiency

    # 3. Лимитирующая мощность (минимум между станцией и авто)
    is_dc = str(station_type).strip().upper() == "DC"
    car_power_limit = (car_max_dc_kw if is_dc else car_max_ac_kw) or (120.0 if is_dc else 11.0)
    effective_power_kw = max(1.0, min(float(station_power_kw or 22.0), float(car_power_limit)))

    # 4. Расчет времени с учетом замедления после 80% на DC
    if is_dc and target_soc > 80:
        soc_up_to_80 = max(0, min(target_soc, 80) - current_soc)
        soc_above_80 = target_soc - max(current_soc, 80)

        e1 = (battery_capacity_kwh * (soc_up_to_80 / 100.0)) / efficiency
        e2 = (battery_capacity_kwh * (soc_above_80 / 100.0)) / efficiency

        time_hours = (e1 / effective_power_kw) + (e2 / (effective_power_kw * 0.45))
    else:
        time_hours = gross_energy_kwh / effective_power_kw

    duration_minutes = max(1, int(round(time_hours * 60)))

    # 5. Расчет стоимости (поминутный тариф либо за кВт·ч)
    if price_per_minute > 0:
        total_cost_rub = round(price_start + (duration_minutes * price_per_minute), 2)
    elif price_per_kwh > 0:
        total_cost_rub = round(price_start + (gross_energy_kwh * price_per_kwh), 2)
    else:
        # Резервная оценка по среднему тарифу (15 ₽ / кВт·ч)
        total_cost_rub = round(price_start + (gross_energy_kwh * 15.0), 2)

    return ChargingEstimate(
        energy_needed_kwh=round(gross_energy_kwh, 2),
        duration_minutes=duration_minutes,
        total_cost_rub=total_cost_rub,
        effective_power_kw=round(effective_power_kw, 1),
    )