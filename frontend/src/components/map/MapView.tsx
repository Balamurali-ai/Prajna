/**
 * ====================================================
 * Map Component — react-leaflet + OpenStreetMap
 * No API key required.
 * ====================================================
 */
import { useEffect } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'

import { useHotspotGeoJSON } from '@hooks/useHotspots'
import { getRiskColor } from '@utils/index'

interface MapViewProps {
  showHotspots?: boolean
  showRiskChoropleth?: boolean
  height?: string
  className?: string
}

// Fix leaflet default icon issue with bundlers
import L from 'leaflet'
import iconUrl from 'leaflet/dist/images/marker-icon.png'
import iconShadow from 'leaflet/dist/images/marker-shadow.png'
L.Marker.prototype.options.icon = L.icon({
  iconUrl,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
})

// India center
const INDIA_CENTER: [number, number] = [20.5937, 78.9629]
const DEFAULT_ZOOM = 5

function HotspotLayer() {
  const { data: geojson } = useHotspotGeoJSON()

  if (!geojson?.features?.length) return null

  return (
    <>
      {geojson.features.map((feature, i) => {
        const coords = feature.geometry?.coordinates as [number, number] | undefined
        if (!coords) return null
        const [lng, lat] = coords
        const props = feature.properties as Record<string, unknown>
        const score = Number(props.hotspot_score ?? 0)
        const color = getRiskColor(score)

        return (
          <CircleMarker
            key={i}
            center={[lat, lng]}
            radius={6 + (score / 100) * 10}
            pathOptions={{
              color,
              fillColor: color,
              fillOpacity: 0.75,
              weight: 1,
            }}
          >
            <Popup>
              <div className="text-xs">
                <div className="font-bold">{String(props.h3_cell ?? 'Hotspot')}</div>
                <div>Score: <b>{score.toFixed(1)}</b></div>
                <div>Rank: #{String(props.rank ?? '—')}</div>
              </div>
            </Popup>
          </CircleMarker>
        )
      })}
    </>
  )
}

function InvalidateOnMount() {
  const map = useMap()
  useEffect(() => {
    setTimeout(() => map.invalidateSize(), 100)
  }, [map])
  return null
}

export function MapView({
  showHotspots = true,
  height = '100%',
  className,
}: MapViewProps) {
  return (
    <div
      className={`relative overflow-hidden rounded-lg border border-border ${className ?? ''}`}
      style={{ height }}
    >
      <MapContainer
        center={INDIA_CENTER}
        zoom={DEFAULT_ZOOM}
        style={{ height: '100%', width: '100%', background: '#1e293b' }}
        zoomControl
      >
        <InvalidateOnMount />
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        {showHotspots && <HotspotLayer />}
      </MapContainer>
    </div>
  )
}

export function buildRiskChoropleth(
  _risk: Array<{ district: string; risk_score: number; risk_rank: number }>,
  _boundaries?: GeoJSON.FeatureCollection
): GeoJSON.FeatureCollection {
  return { type: 'FeatureCollection', features: [] }
}
