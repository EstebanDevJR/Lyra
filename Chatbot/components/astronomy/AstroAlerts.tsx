'use client'

import { useEffect, useState } from 'react'

interface AstroAlert {
  id: string
  title: string
  description: string
  type: 'neo' | 'solar' | 'meteor' | 'eclipse' | 'comet' | 'other'
  severity: 'info' | 'warning' | 'critical'
  date: string
  link?: string
}

const FALLBACK_ALERTS: AstroAlert[] = [
  {
    id: '1',
    title: 'Asteroid 2024 XY Approaching Earth',
    description: 'Near-Earth asteroid will pass within 5.2 million km on December 15. Diameter estimated at 450 meters. No threat to Earth.',
    type: 'neo',
    severity: 'info',
    date: '2025-12-15',
    link: 'https://cneos.jpl.nasa.gov/'
  },
  {
    id: '2',
    title: 'M-class Solar Flare Detected',
    description: 'Moderate solar flare observed from AR3512. Minor radio blackouts possible in high-latitude regions.',
    type: 'solar',
    severity: 'warning',
    date: '2025-11-21',
    link: 'https://spaceweather.com'
  },
  {
    id: '3',
    title: 'Geminid Meteor Shower Peak',
    description: 'Annual Geminid meteor shower peaks tonight. Expect up to 120 meteors per hour under dark skies.',
    type: 'meteor',
    severity: 'info',
    date: '2025-12-14',
    link: 'https://www.amsmeteors.org/'
  }
]

const SEVERITY_STYLES = {
  info: 'bg-blue-600/20 border-blue-500/30 text-blue-400',
  warning: 'bg-yellow-600/20 border-yellow-500/30 text-yellow-400',
  critical: 'bg-red-600/20 border-red-500/30 text-red-400'
}

const TYPE_ICONS = {
  neo: '☄️',
  solar: '☀️',
  meteor: '🌠',
  eclipse: '🌑',
  comet: '☄️',
  other: '⭐'
}

export default function AstroAlerts() {
  const [alerts, setAlerts] = useState<AstroAlert[]>(FALLBACK_ALERTS)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)

  useEffect(() => {
    fetchAlerts()
    // Refresh every 30 minutes
    const interval = setInterval(fetchAlerts, 30 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  const fetchAlerts = async () => {
    const API_URL = '/api/astro-alerts'

    try {
      const response = await fetch(API_URL)
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
      
      const data = await response.json()
      
      if (Array.isArray(data) && data.length > 0) {
        setAlerts(data)
      } else {
        console.warn('No alerts data, using fallback')
      }
    } catch (err) {
      console.error('Error fetching astro alerts:', err)
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="w-full h-24 bg-black/20 backdrop-blur-sm rounded-xl animate-pulse" />
    )
  }

  if (alerts.length === 0) {
    return (
      <div className="w-full bg-black/20 backdrop-blur-sm border border-white/10 rounded-xl p-6 text-center">
        <p className="text-white/50 text-sm">No active alerts</p>
      </div>
    )
  }

  const displayedAlerts = isExpanded ? alerts : alerts.slice(0, 3)
  const hasMoreAlerts = alerts.length > 3

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-1 h-8 bg-gradient-to-b from-[#FF914D] to-[#FFD8A9] rounded-full" />
          <h2 className="text-2xl font-bold text-[#FFD8A9]">⚠️ Active Alerts</h2>
        </div>
        {alerts.length > 0 && (
          <span className="text-sm text-[#98A7DD]">
            {alerts.length} {alerts.length === 1 ? 'alert' : 'alerts'}
          </span>
        )}
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {displayedAlerts.map((alert, index) => (
          <div
            key={alert.id || `alert-${index}`}
            className={`backdrop-blur-md border rounded-2xl p-5 transition-all duration-500 hover:scale-[1.03] hover:shadow-2xl ${SEVERITY_STYLES[alert.severity]}`}
            style={{ 
              animationDelay: `${index * 0.1}s`,
              animation: 'fadeBlurIn 0.6s ease-out forwards'
            }}
          >
            <div className="flex flex-col gap-3">
              <div className="flex items-start justify-between">
                <span className="text-3xl">{TYPE_ICONS[alert.type]}</span>
                <span className="text-xs font-mono px-2 py-1 bg-black/20 rounded">
                  {new Date(alert.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </span>
              </div>
              
              <div>
                <h3 className="font-bold text-white text-lg mb-2 leading-tight">
                  {alert.title}
                </h3>
                
                <p className="text-sm text-white/80 leading-relaxed">
                  {alert.description}
                </p>
                
                {alert.link && (
                  <a
                    href={alert.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 mt-3 text-xs font-semibold hover:underline group"
                  >
                    Learn More
                    <svg className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </a>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {hasMoreAlerts && (
        <div className="mt-6 flex justify-center">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="px-6 py-3 bg-gradient-to-r from-[#FF914D]/20 to-[#FFD8A9]/20 border border-[#FF914D]/40 text-[#FFD8A9] rounded-xl font-semibold hover:from-[#FF914D]/30 hover:to-[#FFD8A9]/30 hover:border-[#FF914D]/60 transition-all duration-300 flex items-center gap-2 group"
          >
            {isExpanded ? (
              <>
                <span>Show Less</span>
                <svg className="w-4 h-4 group-hover:-translate-y-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
              </>
            ) : (
              <>
                <span>View All {alerts.length} Alerts</span>
                <svg className="w-4 h-4 group-hover:translate-y-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  )
}

