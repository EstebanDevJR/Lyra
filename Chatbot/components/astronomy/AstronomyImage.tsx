'use client'

import { useEffect, useState } from 'react'
import Image from 'next/image'

interface AstronomyImage {
  title: string
  explanation: string
  url: string
  hdurl?: string
  date: string
  copyright?: string
  media_type: string
}

const FALLBACK_IMAGE: AstronomyImage = {
  title: 'The Pillars of Creation',
  explanation: 'The iconic Pillars of Creation captured by the James Webb Space Telescope, revealing new details of star formation.',
  url: 'https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=800&auto=format&fit=crop',
  date: new Date().toISOString().split('T')[0],
  media_type: 'image'
}

export default function AstronomyImage() {
  const [image, setImage] = useState<AstronomyImage>(FALLBACK_IMAGE)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)

  useEffect(() => {
    fetchImage()
  }, [])

  const fetchImage = async () => {
    const API_URL = '/api/astronomy-image'
    
    if (!API_URL) {
      console.warn('Astronomy Image API not configured, using fallback')
      setLoading(false)
      return
    }

    try {
      const response = await fetch(API_URL)
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
      
      const data = await response.json()
      
      console.log('AstronomyImage: Received data:', data)
      console.log('AstronomyImage: Has title?', !!data?.title)
      
      // Manejar si viene como array
      let imageData = data;
      if (Array.isArray(data) && data.length > 0) {
        imageData = data[0];
        console.log('AstronomyImage: Extracted from array:', imageData)
      }
      
      if (imageData && imageData.title) {
        setImage(imageData)
        console.log('AstronomyImage: Successfully set image:', imageData.title)
      } else {
        console.warn('AstronomyImage: Invalid image data, using fallback', imageData)
      }
    } catch (err) {
      console.error('AstronomyImage: Error fetching astronomy image:', err)
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="w-full h-[500px] bg-gradient-to-br from-[#282545]/30 to-[#0C0B18]/50 backdrop-blur-sm rounded-2xl animate-pulse flex items-center justify-center border border-[#98A7DD]/10">
        <div className="text-[#98A7DD]/50 text-sm">Loading today's cosmic view...</div>
      </div>
    )
  }

  return (
    <div className="w-full bg-gradient-to-br from-[#1a1825]/80 to-[#282545]/60 backdrop-blur-md border border-[#98A7DD]/20 hover:border-[#FF914D]/50 rounded-2xl overflow-hidden group hover:shadow-2xl hover:shadow-[#FF914D]/20 transition-all duration-500">
      {/* Image */}
      <div className="relative h-[500px] w-full overflow-hidden">
        {image.media_type === 'image' ? (
          <>
            <Image
              src={image.hdurl || image.url}
              alt={image.title}
              fill
              className="object-cover group-hover:scale-110 transition-transform duration-700"
              sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            />
            {/* Glow overlay on hover */}
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
              <div className="absolute inset-0 bg-gradient-to-tr from-[#FF914D]/20 via-transparent to-[#FFD8A9]/20" />
            </div>
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-[#282545] to-[#0C0B18]">
            <div className="text-center space-y-2">
              <svg className="w-16 h-16 mx-auto text-[#98A7DD]/30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-white/50 text-sm">Video content</span>
            </div>
          </div>
        )}
        
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#0C0B18] via-[#0C0B18]/30 to-transparent" />
        
        {/* Date Badge */}
        <div className="absolute top-6 right-6 px-4 py-2 bg-[#FF914D]/90 backdrop-blur-md rounded-full text-[#0C0B18] text-sm font-bold shadow-lg">
          {new Date(image.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
        </div>
      </div>

      {/* Content */}
      <div className="p-8">
        <h3 className="text-2xl font-bold text-[#FFD8A9] mb-3 leading-tight group-hover:text-[#FF914D] transition-colors">
          {image.title}
        </h3>
        
        {image.copyright && (
          <p className="text-xs text-[#98A7DD]/70 mb-4 flex items-center gap-2">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
            </svg>
            © {image.copyright}
          </p>
        )}
        
        <p className={`text-sm text-[#98A7DD] leading-relaxed ${!isExpanded && 'line-clamp-4'}`}>
          {image.explanation}
        </p>
        
        {image.explanation.length > 200 && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="mt-4 text-sm font-semibold text-[#FF914D] hover:text-[#FFD8A9] transition-colors inline-flex items-center gap-1 group/btn"
          >
            {isExpanded ? (
              <>
                Show less
                <svg className="w-4 h-4 group-hover/btn:-translate-y-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
              </>
            ) : (
              <>
                Read full description
                <svg className="w-4 h-4 group-hover/btn:translate-y-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </>
            )}
          </button>
        )}
      </div>
    </div>
  )
}

