/**
 * ====================================================
 * Mapbox Map Component
 * ====================================================
 * Renders hotspots and risk choropleth on Mapbox GL JS.
 * ====================================================
 */
import { useEffect, useRef, useState } from 'react'
import mapboxgl from 'mapbox-gl'
import { MapPin } from 'lucide-react'

import { useHotspotGeoJSON } from '@hooks/useHotspots'
import { useRiskRankings } from '@hooks/useRisk'
import { config } from '@config/index'
import { getRiskColor, getRiskLevel } from '@utils/index'


interface MapViewProps {
  onDistrictClick?: (district: string) => void
  showHotspots?: boolean
  showRiskChoropleth?: boolean
  height?: string
  className?: string
}

export function MapView({
  onDistrictClick,
  showHotspots = true,
  showRiskChoropleth = true,
  height = '100%',
  className,
}: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<mapboxgl.Map | null>(null)
  const [mapReady, setMapReady] = useState(false)

  const { data: hotspotsGeoJSON } = useHotspotGeoJSON({ enabled: showHotspots })
  const { data: riskData } = useRiskRankings(undefined, { enabled: showRiskChoropleth })

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return

    mapboxgl.accessToken = config.mapbox.token

    if (!config.mapbox.token) {
      console.warn('Mapbox token missing — map will not render')
      return
    }

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: `mapbox://styles/mapbox/${config.mapbox.style}`,
      center: config.mapbox.defaultCenter,
      zoom: config.mapbox.defaultZoom,
      attributionControl: true,
    })

    map.current.addControl(new mapboxgl.NavigationControl(), 'top-right')
    map.current.addControl(new mapboxgl.FullscreenControl(), 'top-right')
    map.current.addControl(
      new mapboxgl.ScaleControl({ maxWidth: 100, unit: 'metric' }),
      'bottom-left'
    )

    map.current.on('load', () => setMapReady(true))

    return () => {
      map.current?.remove()
      map.current = null
    }
  }, [])

  // Add hotspot layer
  useEffect(() => {
    if (!mapReady || !map.current || !showHotspots || !hotspotsGeoJSON) return
    const m = map.current

    if (m.getSource('hotspots')) {
      ;(m.getSource('hotspots') as mapboxgl.GeoJSONSource).setData(
        hotspotsGeoJSON as GeoJSON.FeatureCollection
      )
      return
    }

    m.addSource('hotspots', {
      type: 'geojson',
      data: hotspotsGeoJSON as GeoJSON.FeatureCollection,
    })

    m.addLayer({
      id: 'hotspot-heat',
      type: 'heatmap',
      source: 'hotspots',
      maxzoom: 14,
      paint: {
        'heatmap-weight': [
          'interpolate',
          ['linear'],
          ['get', 'hotspot_score'],
          0, 0,
          100, 1,
        ],
        'heatmap-intensity': [
          'interpolate',
          ['linear'],
          ['zoom'],
          0, 1,
          14, 3,
        ],
        'heatmap-color': [
          'interpolate',
          ['linear'],
          ['heatmap-density'],
          0, 'rgba(0,0,255,0)',
          0.2, 'rgba(16,185,129,0.4)',
          0.4, 'rgba(234,179,8,0.6)',
          0.6, 'rgba(249,115,22,0.8)',
          1, 'rgba(239,68,68,1)',
        ],
        'heatmap-radius': [
          'interpolate',
          ['linear'],
          ['zoom'],
          0, 8,
          14, 30,
        ],
        'heatmap-opacity': [
          'interpolate',
          ['linear'],
          ['zoom'],
          7, 0.8,
          14, 0.3,
        ],
      },
    })

    m.addLayer({
      id: 'hotspot-points',
      type: 'circle',
      source: 'hotspots',
      minzoom: 10,
      paint: {
        'circle-radius': [
          'interpolate',
          ['linear'],
          ['get', 'hotspot_score'],
          0, 4,
          100, 12,
        ],
        'circle-color': [
          'interpolate',
          ['linear'],
          ['get', 'hotspot_score'],
          0, '#10b981',
          40, '#eab308',
          60, '#f97316',
          80, '#ef4444',
        ],
        'circle-stroke-color': '#ffffff',
        'circle-stroke-width': 1,
        'circle-opacity': 0.85,
      },
    })

    // Click handler
    m.on('click', 'hotspot-points', (e) => {
      const feature = e.features?.[0]
      if (!feature) return
      const props = feature.properties as Record<string, unknown>
      new mapboxgl.Popup()
        .setLngLat(e.lngLat)
        .setHTML(
          `<div class="text-xs">
            <div class="font-bold">${props.h3_cell ?? 'Hotspot'}</div>
            <div>Score: <b>${(props.hotspot_score as number)?.toFixed(1) ?? '—'}</b></div>
            <div>Rank: #${props.rank ?? '—'}</div>
          </div>`
        )
        .addTo(m)
    })

    m.on('mouseenter', 'hotspot-points', () => {
      m.getCanvas().style.cursor = 'pointer'
    })
    m.on('mouseleave', 'hotspot-points', () => {
      m.getCanvas().style.cursor = ''
    })
  }, [mapReady, hotspotsGeoJSON, showHotspots])

  // Add risk marker overlay
  useEffect(() => {
    if (!mapReady || !map.current || !riskData) return
    const m = map.current
    // Markers are simple — district centroids not provided in predictions CSV,
    // so we leave this as a future enhancement when district boundaries are available.
  }, [mapReady, riskData])

  return (
    <div className={`relative overflow-hidden rounded-lg border border-border ${className ?? ''}`} style={{ height }}>
      <div ref={mapContainer} className="absolute inset-0" />
      {!config.mapbox.token && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="text-center">
            <MapPin className="mx-auto h-12 w-12 text-muted-foreground" />
            <p className="mt-3 text-sm font-medium">Mapbox token not configured</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Add VITE_MAPBOX_PUBLIC_TOKEN to your .env
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

// Helper: build a feature collection from risk data (for choropleth)
// Note: requires district boundaries GeoJSON — to be added when available.
export function buildRiskChoropleth(
  risk: Array<{ district: string; risk_score: number; risk_rank: number }>,
  boundaries?: GeoJSON.FeatureCollection
): GeoJSON.FeatureCollection {
  if (!boundaries) {
    return { type: 'FeatureCollection', features: [] }
  }
  const scoreMap = new Map(
    risk.map((r) => [r.district.toLowerCase(), r.risk_score])
  )
  const features: GeoJSON.Feature[] = boundaries.features.map((f) => {
    const district = ((f.properties as Record<string, unknown>)?.name as string) ?? ''
    const score = scoreMap.get(district.toLowerCase()) ?? 0
    return {
      ...f,
      properties: {
        ...f.properties,
        risk_score: score,
        risk_level: getRiskLevel(score),
        fill_color: getRiskColor(score),
      },
    }
  })
  return { type: 'FeatureCollection', features }
}

