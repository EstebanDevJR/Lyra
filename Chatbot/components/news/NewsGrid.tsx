import React, { useEffect, useState } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { ExternalLink, RefreshCw, Newspaper } from 'lucide-react'

interface NewsItem {
  title: string
  description: string
  link: string
  imageUrl?: string
  source?: string
  date?: string
}

// Datos de ejemplo por si falla la carga o no hay URL configurada
const FALLBACK_NEWS: NewsItem[] = [
  {
    title: "Descubrimiento en la Nebulosa de Orión",
    description: "El telescopio James Webb revela nuevos detalles sobre la formación estelar en la nebulosa más cercana a la Tierra.",
    link: "https://www.nasa.gov",
    source: "NASA",
    date: "Hace 2 horas",
    imageUrl: "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?q=80&w=2072&auto=format&fit=crop"
  },
  {
    title: "Misión Artemis II: Preparativos",
    description: "La tripulación de Artemis II continúa su entrenamiento para la próxima misión lunar tripulada.",
    link: "https://www.nasa.gov",
    source: "SpaceX",
    date: "Hace 5 horas",
    imageUrl: "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2072&auto=format&fit=crop"
  },
  {
    title: "Nuevos exoplanetas habitables",
    description: "Astrónomos identifican tres nuevos candidatos en la zona habitable de una estrella enana roja cercana.",
    link: "https://www.esa.int",
    source: "ESA",
    date: "Ayer",
    imageUrl: "https://images.unsplash.com/photo-1614730341194-75c6074065db?q=80&w=2074&auto=format&fit=crop"
  },
  {
    title: "Actividad Solar Reciente",
    description: "Se detectan fuertes llamaradas solares que podrían causar auroras boreales en latitudes bajas.",
    link: "https://www.spaceweather.com",
    source: "SpaceWeather",
    date: "Hace 12 horas",
    imageUrl: "https://images.unsplash.com/photo-1532094349884-543bc11b234d?q=80&w=2070&auto=format&fit=crop"
  }
]

export default function NewsGrid() {
  const [news, setNews] = useState<NewsItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  // URL interna de Next.js (actúa como proxy)
  // Si no hay webhook configurado, usará fallback
  const API_URL = process.env.NEXT_PUBLIC_N8N_NEWS_WEBHOOK ? '/api/news' : ''

  const fetchNews = async () => {
    setLoading(true)
    setError(false)
    try {
      if (!API_URL) {
        // Simular carga si no hay URL configurada
        await new Promise(resolve => setTimeout(resolve, 1500))
        setNews(FALLBACK_NEWS)
        return
      }

      const response = await fetch(API_URL)
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
      
      const text = await response.text()
      if (!text) throw new Error('Empty response received')
      
      try {
        const data = JSON.parse(text)
        console.log('News Data received (raw):', data)

        let newsArray = []
        
        if (Array.isArray(data)) {
          console.log('Data is direct array, length:', data.length)
          newsArray = data
        } else if (data && Array.isArray(data.data)) {
          console.log('Data is in data.data, length:', data.data.length)
          newsArray = data.data
        } else if (data && Array.isArray(data.items)) {
          console.log('Data is in data.items, length:', data.items.length)
          newsArray = data.items
        } else if (typeof data === 'object' && data !== null) {
           // Check if it's a single news item
           if (data.title && (data.description || data.link)) {
             console.log('Data is single object, wrapping in array')
             newsArray = [data]
           } else {
             // Try to find any array property as a fallback
             const possibleArray = Object.values(data).find(val => Array.isArray(val));
             if (possibleArray) {
               console.log('Found array in object values, length:', (possibleArray as any[]).length)
               newsArray = possibleArray as any[];
             }
           }
        }

        console.log('Final newsArray to set:', newsArray)

        if (newsArray.length > 0) {
          setNews(newsArray)
        } else {
          console.warn('Data structure not recognized or empty array, using fallback', data)
          setNews(FALLBACK_NEWS)
        }
      } catch (e) {
        console.warn('Invalid JSON response, using fallback', e)
        setNews(FALLBACK_NEWS)
      }
    } catch (err) {
      console.error('Error fetching news:', err)
      setError(true)
      setNews(FALLBACK_NEWS) // Fallback en caso de error
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchNews()
  }, [])

  return (
    <div className="w-full">
      <div className="flex items-center justify-end mb-6">
        <Button 
          onClick={fetchNews} 
          variant="outline" 
          size="sm"
          className="bg-[#282545]/50 border-[#98A7DD]/30 text-[#FFD8A9] hover:bg-[#282545] hover:text-[#FF914D] transition-colors"
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading && news.length === 0 ? (
          // Skeletons
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-80 rounded-2xl bg-[#282545]/30 animate-pulse border border-[#98A7DD]/10" />
          ))
        ) : (
          news.map((item, index) => (
            <Card 
              key={index}
              className="group relative overflow-hidden bg-gradient-to-br from-[#1a1825]/80 to-[#282545]/60 border-[#98A7DD]/20 hover:border-[#FF914D]/50 transition-all duration-500 hover:shadow-2xl hover:shadow-[#FF914D]/20 hover:-translate-y-2 backdrop-blur-md rounded-2xl"
              style={{ 
                animationDelay: `${index * 0.05}s`,
                animation: 'fadeBlurIn 0.6s ease-out forwards'
              }}
            >
              {/* Glow Effect */}
              <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                <div className="absolute inset-0 bg-gradient-to-tr from-[#FF914D]/10 via-transparent to-[#FFD8A9]/10 rounded-2xl" />
              </div>

              <div className="relative">
                <div className="aspect-video w-full overflow-hidden relative">
                  {item.imageUrl ? (
                    <img 
                      src={item.imageUrl} 
                      alt={item.title}
                      className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                    />
                  ) : (
                    <div className="w-full h-full bg-gradient-to-br from-[#282545] to-[#0C0B18] flex items-center justify-center">
                      <Newspaper className="w-12 h-12 text-[#98A7DD]/30" />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-[#0C0B18] via-[#0C0B18]/40 to-transparent" />
                  
                  <div className="absolute bottom-3 left-4 right-4 flex justify-between items-end">
                    {item.source && (
                      <span className="text-xs font-semibold px-3 py-1.5 rounded-full bg-[#FF914D]/90 text-[#0C0B18] border border-[#FFD8A9]/50 backdrop-blur-md shadow-lg">
                        {item.source}
                      </span>
                    )}
                    {item.date && (
                      <span className="text-xs text-[#FFD8A9] font-mono bg-[#0C0B18]/50 px-2 py-1 rounded backdrop-blur-sm">
                        {item.date}
                      </span>
                    )}
                  </div>
                </div>

                <div className="p-6">
                  <h3 className="text-xl font-bold text-[#FFD8A9] mb-3 line-clamp-2 group-hover:text-[#FF914D] transition-colors leading-tight">
                    {item.title}
                  </h3>
                  <p className="text-sm text-[#98A7DD] line-clamp-3 mb-4 leading-relaxed">
                    {item.description}
                  </p>
                  
                  <a 
                    href={item.link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-sm font-semibold text-[#FF914D] hover:text-[#FFD8A9] transition-colors group/link"
                  >
                    Read Full Story 
                    <ExternalLink className="w-4 h-4 group-hover/link:translate-x-0.5 group-hover/link:-translate-y-0.5 transition-transform" />
                  </a>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}

