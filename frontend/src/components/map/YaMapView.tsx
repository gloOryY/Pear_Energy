'use client';
import { useEffect, useRef, useState } from 'react';
import { loadYmaps, STATUS_COLOR } from '../../lib/ymaps';
import type { StationShort } from '../../types';

interface Props {
  stations: StationShort[];
  apiKey: string;
  center?: [number, number];
  zoom?: number;
  onSelect: (s: StationShort) => void;
  searchQuery?: string;
  userLocation?: [number, number] | null;
}

export default function YaMapView({ stations, apiKey, center = [55.75, 37.61], zoom = 5, onSelect, searchQuery, userLocation }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const clustererRef = useRef<any>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    loadYmaps(apiKey).then((ymaps) => {
      if (cancelled || !containerRef.current) return;
      const map = new ymaps.Map(containerRef.current, { center, zoom, controls: ['zoomControl', 'geolocationControl', 'typeSelector'] }, { suppressMapOpenBlock: true });
      map.behaviors.enable('scrollZoom');
      mapRef.current = map;
      const clusterer = new ymaps.Clusterer({ groupByCoordinates: false, clusterDisableClickZoom: false });
      clustererRef.current = clusterer;
      map.geoObjects.add(clusterer);
      setReady(true);
    }).catch(setError);
    return () => { cancelled = true; };
  }, [apiKey, center, zoom]);

  useEffect(() => {
    if (!ready || !window.ymaps) return;
    const ymaps = window.ymaps;
    clustererRef.current?.removeAll();
    for (const s of stations) {
      const pm = new ymaps.Placemark([Number(s.latitude), Number(s.longitude)], {
        balloonContentHeader: s.name,
        balloonContentBody: `${s.city ?? ''}<br/>${s.tariff_per_kwh} ₽/кВт⋅ч`,
      }, {
        preset: 'islands#circleIcon',
        iconColor: STATUS_COLOR[s.status] ?? '#71717a',
      });
      pm.events.add('click', () => onSelect(s));
      clustererRef.current?.add(pm);
    }
    if (stations.length) {
      const coords = stations.map((s) => [Number(s.latitude), Number(s.longitude)]);
      mapRef.current.setBounds(ymaps.util.bounds.fromPoints(coords), { checkZoomRange: true, zoomMargin: 40 });
    }
  }, [ready, stations, onSelect]);

  useEffect(() => {
    if (!ready || !searchQuery || !window.ymaps) return;
    window.ymaps.geocode(searchQuery, { results: 1 }).then((res: any) => {
      const first = res.geoObjects.get(0);
      if (first) mapRef.current.setCenter(first.geometry.getCoordinates(), 12, { duration: 400 });
    }).catch(() => {});
  }, [ready, searchQuery]);

  useEffect(() => {
    if (ready && userLocation) {
      mapRef.current.setCenter(userLocation, 13, { duration: 400 });
      const pm = new window.ymaps.Placemark(userLocation, '', { preset: 'islands#blueDotCircleIcon' });
      mapRef.current.geoObjects.add(pm);
    }
  }, [ready, userLocation]);

  if (error) return <div className="flex items-center justify-center h-full text-zinc-400">{error}</div>;
  return <div ref={containerRef} className="w-full h-full .ymaps-2-1-47-map rounded-2xl" />;
}
