"use client";

import { useEffect, useRef } from "react";
import "ol/ol.css";
import Map from "ol/Map";
import View from "ol/View";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import OSM from "ol/source/OSM";
import VectorSource from "ol/source/Vector";
import Feature from "ol/Feature";
import Point from "ol/geom/Point";
import { fromLonLat } from "ol/proj";
import { Style, Circle as CircleStyle, Fill, Stroke, Text } from "ol/style";
import { STATUS_COLOR } from "../../lib/ymaps";
import type { StationShort } from "../../types";

interface Props {
  stations?: StationShort[] | { items?: StationShort[] };
  apiKey?: string;
  center?: [number, number];
  zoom?: number;
  onSelect?: (s: StationShort) => void;
  searchQuery?: string;
  userLocation?: [number, number] | null;
}

export default function YaMapView({
  stations = [],
  center = [55.75, 37.61],
  zoom = 5,
  onSelect,
  searchQuery,
  userLocation,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);
  const stationsSourceRef = useRef<VectorSource>(new VectorSource());
  const userSourceRef = useRef<VectorSource>(new VectorSource());
  const onSelectRef = useRef(onSelect);

  useEffect(() => {
    onSelectRef.current = onSelect;
  }, [onSelect]);

  // 1. Инициализация карты OpenLayers
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const stationsLayer = new VectorLayer({
      source: stationsSourceRef.current,
      style: (feature) => {
        const status = feature.get("status") as string;
        const color = STATUS_COLOR?.[status] ?? "#22c55e";
        return new Style({
          image: new CircleStyle({
            radius: 9,
            fill: new Fill({ color }),
            stroke: new Stroke({ color: "#ffffff", width: 2 }),
          }),
          text: new Text({
            text: feature.get("name") || "",
            offsetY: -16,
            font: "500 12px sans-serif",
            fill: new Fill({ color: "#ffffff" }),
            stroke: new Stroke({ color: "#18181b", width: 3 }),
          }),
        });
      },
    });

    const userLayer = new VectorLayer({
      source: userSourceRef.current,
      style: new Style({
        image: new CircleStyle({
          radius: 8,
          fill: new Fill({ color: "#3b82f6" }),
          stroke: new Stroke({ color: "#ffffff", width: 2.5 }),
        }),
      }),
    });

    const map = new Map({
      target: containerRef.current,
      layers: [
        new TileLayer({ source: new OSM() }),
        stationsLayer,
        userLayer,
      ],
      view: new View({
        center: fromLonLat([center[1], center[0]]),
        zoom,
      }),
    });

    map.on("singleclick", (evt) => {
      const feature = map.forEachFeatureAtPixel(evt.pixel, (f) => f);
      if (feature && feature.get("station") && onSelectRef.current) {
        onSelectRef.current(feature.get("station"));
      }
    });

    map.on("pointermove", (evt) => {
      if (evt.dragging) return;
      const hit = map.hasFeatureAtPixel(evt.pixel);
      map.getTargetElement().style.cursor = hit ? "pointer" : "";
    });

    mapRef.current = map;

    return () => {
      map.setTarget(undefined);
      mapRef.current = null;
    };
  }, []);

  // 2. Безопасное обновление маркеров станций
  useEffect(() => {
    const source = stationsSourceRef.current;
    source.clear();

    // Защита: приводим stations к массиву в любом случае
    const stationList: StationShort[] = Array.isArray(stations)
      ? stations
      : Array.isArray((stations as any)?.items)
      ? (stations as any).items
      : [];

    for (const s of stationList) {
      const lat = Number(s.latitude);
      const lon = Number(s.longitude);
      if (isNaN(lat) || isNaN(lon)) continue;

      const feature = new Feature({
        geometry: new Point(fromLonLat([lon, lat])),
        station: s,
        name: s.name,
        status: s.status,
      });
      source.addFeature(feature);
    }

    if (stationList.length > 0 && mapRef.current) {
      const extent = source.getExtent();
      if (extent && !extent.some((v) => !isFinite(v))) {
        mapRef.current.getView().fit(extent, {
          padding: [50, 50, 50, 50],
          maxZoom: 15,
          duration: 400,
        });
      }
    }
  }, [stations]);

  // 3. Поиск по адресу через Nominatim
  useEffect(() => {
    if (!searchQuery || !mapRef.current) return;
    fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
        searchQuery
      )}&limit=1&accept-language=ru`
    )
      .then((r) => r.json())
      .then((data) => {
        if (data && data[0] && mapRef.current) {
          const lat = parseFloat(data[0].lat);
          const lon = parseFloat(data[0].lon);
          mapRef.current.getView().animate({
            center: fromLonLat([lon, lat]),
            zoom: 12,
            duration: 400,
          });
        }
      })
      .catch(() => {});
  }, [searchQuery]);

  // 4. Отображение геолокации пользователя
  useEffect(() => {
    const source = userSourceRef.current;
    source.clear();

    if (userLocation && mapRef.current) {
      const [lat, lon] = userLocation;
      const coord = fromLonLat([lon, lat]);
      source.addFeature(new Feature({ geometry: new Point(coord) }));
      mapRef.current.getView().animate({
        center: coord,
        zoom: 13,
        duration: 400,
      });
    }
  }, [userLocation]);

  return <div ref={containerRef} className="w-full h-full min-h-[500px] rounded-2xl overflow-hidden" />;
}