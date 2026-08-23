export interface StationShort {
  id: string;
  public_id: string;
  name: string;
  status: string;
  latitude: string;
  longitude: string;
  max_power_kw: string;
  tariff_per_kwh: string;
  supports_booking: boolean;
  city: string | null;
  address: string | null;
  photo: string | null;
}

export interface StationDetail extends Omit<StationShort, 'photo'> {
  serial_number: string;
  connector_type: string;
  max_current_a: string;
  tariff_per_minute_idle: string;
  min_launch_amount: string;
  booking_amount: string;
  is_active: boolean;
  parking_info: string;
  last_seen_at: string | null;
  location_name: string;
  description: string;
  amenities: string[];
  schedule: any;
  venue_types: string[];
  photos: string[];
  connectors: { id: string; connector_number: number; type: string; max_power_kw: string; status: string }[];
}
