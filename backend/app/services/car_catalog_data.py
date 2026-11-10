"""Справочник заводских характеристик электромобилей для первичного наполнения базы."""

CARS_CATALOG = [
    # Zeekr
    {
        "make": "Zeekr",
        "model": "001 (100 кВт·ч)",
        "battery_capacity_kwh": 100.0,
        "max_ac_power_kw": 22.0,
        "max_dc_power_kw": 200.0,
        "connector_type": "GB/T",
    },
    {
        "make": "Zeekr",
        "model": "001 (86 кВт·ч)",
        "battery_capacity_kwh": 86.0,
        "max_ac_power_kw": 11.0,
        "max_dc_power_kw": 180.0,
        "connector_type": "GB/T",
    },
    {
        "make": "Zeekr",
        "model": "007",
        "battery_capacity_kwh": 75.0,
        "max_ac_power_kw": 11.0,
        "max_dc_power_kw": 250.0,
        "connector_type": "GB/T",
    },
    {
        "make": "Zeekr",
        "model": "X",
        "battery_capacity_kwh": 66.0,
        "max_ac_power_kw": 11.0,
        "max_dc_power_kw": 150.0,
        "connector_type": "GB/T",
    },
    {
        "make": "Zeekr",
        "model": "009",
        "battery_capacity_kwh": 140.0,
        "max_ac_power_kw": 22.0,
        "max_dc_power_kw": 250.0,
        "connector_type": "GB/T",
    },

    # Geely
    {
        "make": "Geely",
        "model": "EX5 / Galaxy E5 (60 кВт·ч)",
        "battery_capacity_kwh": 60.22,
        "max_ac_power_kw": 11.0,
        "max_dc_power_kw": 85.0,
        "connector_type": "GB/T",
    },
    {
        "make": "Geely",
        "model": "Galaxy E8",
        "battery_capacity_kwh": 76.0,
        "max_ac_power_kw": 11.0,
        "max_dc_power_kw": 180.0,
        "connector_type": "GB/T",
    },
    {
        "make": "Geely",
        "model": "Geometry C (70 кВт·ч)",
        "battery_capacity_kwh": 70.0,
        "max_ac_power_kw": 11.0,
        "max_dc_power_kw": 75.0,
        "connector_type": "GB/T",
    },

    # Tesla
    {
        "make": "Tesla",
        "model": "Model 3 Long Range",
        "battery_capacity_kwh": 78.1,
        "max_ac_power_kw": 11.0,
        "max_dc_power_kw": 250.0,
        "connector_type": "CCS2",
    },
    {
        "make": "Tesla",
        "model": "Model Y Long Range",
        "battery_capacity_kwh": 78.1,
        "max_ac_power_kw": 11.0,
        "max_dc_power_kw": 250.0,
        "connector_type": "CCS2",
    },
    {
        "make": "Tesla",
        "model": "Model X Plaid",
        "battery_capacity_kwh": 100.0,
        "max_ac_power_kw": 16.5,
        "max_dc_power_kw": 250.0,
        "connector_type": "CCS2",
    },

    # BYD
    {
        "make": "BYD",
        "model": "Song Plus EV (71 кВт·ч)",
        "battery_capacity_kwh": 71.7,
        "max_ac_power_kw": 7.0,
        "max_dc_power_kw": 90.0,
        "connector_type": "GB/T",
    },
    {
        "make": "BYD",
        "model": "Han EV",
        "battery_capacity_kwh": 85.4,
        "max_ac_power_kw": 11.0,
        "max_dc_power_kw": 120.0,
        "connector_type": "GB/T",
    },
    {
        "make": "BYD",
        "model": "Seal",
        "battery_capacity_kwh": 82.5,
        "max_ac_power_kw": 11.0,
        "max_dc_power_kw": 150.0,
        "connector_type": "GB/T",
    },

    # Li Auto (REEV)
    {
        "make": "Li Auto",
        "model": "L7 / L8 / L9 (REEV)",
        "battery_capacity_kwh": 42.8,
        "max_ac_power_kw": 7.0,
        "max_dc_power_kw": 75.0,
        "connector_type": "GB/T",
    },

    # Voyah
    {
        "make": "Voyah",
        "model": "Free EV",
        "battery_capacity_kwh": 106.0,
        "max_ac_power_kw": 11.0,
        "max_dc_power_kw": 120.0,
        "connector_type": "GB/T",
    },
    {
        "make": "Voyah",
        "model": "Dream EV",
        "battery_capacity_kwh": 108.7,
        "max_ac_power_kw": 11.0,
        "max_dc_power_kw": 120.0,
        "connector_type": "GB/T",
    },

    # Avatr
    {
        "make": "Avatr",
        "model": "11",
        "battery_capacity_kwh": 116.0,
        "max_ac_power_kw": 11.0,
        "max_dc_power_kw": 240.0,
        "connector_type": "GB/T",
    },

    # Volkswagen
    {
        "make": "Volkswagen",
        "model": "ID.4 Crozz (84 кВт·ч)",
        "battery_capacity_kwh": 84.8,
        "max_ac_power_kw": 11.0,
        "max_dc_power_kw": 100.0,
        "connector_type": "GB/T",
    },
    {
        "make": "Volkswagen",
        "model": "ID.6 Crozz",
        "battery_capacity_kwh": 84.8,
        "max_ac_power_kw": 11.0,
        "max_dc_power_kw": 100.0,
        "connector_type": "GB/T",
    },

    # Evolute / Москвич
    {
        "make": "Evolute",
        "model": "i-Joy",
        "battery_capacity_kwh": 53.0,
        "max_ac_power_kw": 7.0,
        "max_dc_power_kw": 45.0,
        "connector_type": "CCS2",
    },
    {
        "make": "Москвич",
        "model": "3e",
        "battery_capacity_kwh": 65.7,
        "max_ac_power_kw": 11.0,
        "max_dc_power_kw": 75.0,
        "connector_type": "GB/T",
    },
]