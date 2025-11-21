'use client'

import { useEffect, useState } from 'react'

interface ResearchPaper {
  id: string
  title: string
  authors: string
  abstract: string
  summary?: string
  published: string
  link: string
  category: string
}

const FALLBACK_PAPERS: ResearchPaper[] = [
  {
    id: '2511.12345',
    title: 'Direct Imaging of Black Hole Photon Rings with Next-Generation EHT',
    authors: 'Johnson, M.D., Narayan, R., Doeleman, S.S., et al.',
    abstract: 'We present simulations of photon ring imaging with the next-generation Event Horizon Telescope...',
    summary: 'Researchers demonstrate that the next-generation Event Horizon Telescope could directly image the photon rings around supermassive black holes, providing unprecedented tests of general relativity.',
    published: '2025-11-19',
    link: 'https://arxiv.org/abs/2511.12345',
    category: 'Black Holes'
  },
  {
    id: '2511.12346',
    title: 'Discovery of Ultra-High-Energy Gamma Rays from Galactic Center',
    authors: 'Chen, Y., Liu, H., Wang, S., et al.',
    abstract: 'LHAASO observations reveal gamma rays exceeding 1 PeV from the Galactic Center region...',
    summary: 'Chinese astronomers detected ultra-high-energy gamma rays from the Milky Way center, suggesting the presence of a powerful particle accelerator near our galaxy\'s supermassive black hole.',
    published: '2025-11-20',
    link: 'https://arxiv.org/abs/2511.12346',
    category: 'High Energy'
  },
  {
    id: '2511.12347',
    title: 'JWST Reveals Population III Star Candidates at z > 10',
    authors: 'Martinez, A., Windhorst, R., Cohen, S., et al.',
    abstract: 'We identify three candidates for Population III stars in ultra-deep JWST/NIRCam imaging...',
    summary: 'James Webb Space Telescope may have found the first generation of stars in the universe, formed just 200 million years after the Big Bang.',
    published: '2025-11-18',
    link: 'https://arxiv.org/abs/2511.12347',
    category: 'Galaxies'
  },
  {
    id: '2511.12348',
    title: 'Gravitational Wave Memory from Binary Black Hole Mergers',
    authors: 'Patel, K., Flanagan, É.É., Thorne, K.S.',
    abstract: 'We calculate the gravitational wave memory effect for eccentric binary black hole mergers...',
    summary: 'New calculations show that LIGO-Virgo-KAGRA could detect the permanent spacetime distortion left behind by merging black holes, opening a new window on gravitational physics.',
    published: '2025-11-16',
    link: 'https://arxiv.org/abs/2511.12348',
    category: 'Gravitational Waves'
  },
  {
    id: '2511.12349',
    title: 'Dark Matter Annihilation in Dwarf Galaxies: Fermi-LAT Constraints',
    authors: 'Anderson, B., Bertone, G., Strigari, L.E.',
    abstract: 'We present updated constraints on WIMP dark matter from 14 years of Fermi-LAT observations...',
    summary: 'Analysis of gamma-ray data from dwarf galaxies places the tightest constraints yet on dark matter particle properties, ruling out several popular theoretical models.',
    published: '2025-11-14',
    link: 'https://arxiv.org/abs/2511.12349',
    category: 'Dark Matter'
  }
]

export default function ResearchPapers() {
  const [papers, setPapers] = useState<ResearchPaper[]>(FALLBACK_PAPERS)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  useEffect(() => {
    fetchPapers()
  }, [])

  const fetchPapers = async () => {
    const API_URL = '/api/research-papers'

    try {
      const response = await fetch(API_URL)
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
      
      const data = await response.json()
      
      console.log('ResearchPapers: Received data type:', Array.isArray(data) ? 'Array' : typeof data)
      console.log('ResearchPapers: Data length:', Array.isArray(data) ? data.length : 'N/A')
      console.log('ResearchPapers: First item:', data && Array.isArray(data) && data.length > 0 ? data[0] : 'N/A')
      
      if (Array.isArray(data) && data.length > 0) {
        // Validar y limpiar los datos recibidos
        const validPapers = data
          .filter(paper => {
            const isValid = paper && (paper.title || paper.summary || paper.abstract)
            if (!isValid) {
              console.warn('ResearchPapers: Filtered out invalid paper:', paper)
            }
            return isValid
          })
          .map((paper, index) => ({
            id: paper.id || `paper-${index}-${Date.now()}`,
            title: paper.title || 'Untitled Paper',
            authors: paper.authors || 'Unknown Authors',
            abstract: paper.abstract || paper.summary || '',
            summary: paper.summary || paper.abstract?.substring(0, 200) + '...' || '',
            published: paper.published || new Date().toISOString().split('T')[0],
            link: paper.link || '#',
            category: paper.category || 'Astrophysics'
          }))
        
        console.log('ResearchPapers: Valid papers after filtering:', validPapers.length)
        
        if (validPapers.length > 0) {
          setPapers(validPapers)
          console.log('ResearchPapers: Successfully set papers:', validPapers.length)
        } else {
          console.warn('ResearchPapers: No valid papers after filtering, using fallback')
        }
      } else {
        console.warn('ResearchPapers: Data is not a valid array or is empty, using fallback')
        console.warn('ResearchPapers: Data received:', data)
      }
    } catch (err) {
      console.error('ResearchPapers: Error fetching research papers:', err)
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  const categories = ['all', ...Array.from(new Set(papers.map(p => p.category)))]
  const filteredPapers = selectedCategory === 'all' 
    ? papers 
    : papers.filter(p => p.category === selectedCategory)

  if (loading) {
    return (
      <div className="w-full space-y-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-32 bg-black/20 backdrop-blur-sm rounded-xl animate-pulse" />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="w-full bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center">
        <p className="text-red-400 text-sm">Error loading research papers. Using fallback data.</p>
      </div>
    )
  }

  if (filteredPapers.length === 0) {
    return (
      <div className="w-full bg-black/20 backdrop-blur-sm border border-white/10 rounded-xl p-6 text-center">
        <p className="text-white/50 text-sm">No papers found for the selected category.</p>
      </div>
    )
  }

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Recent Research</h2>
        
        {/* Category Filter */}
        <div className="flex gap-2">
          {categories.map((cat, index) => (
            <button
              key={cat || `category-${index}`}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1 text-xs rounded-full transition-all ${
                selectedCategory === cat
                  ? 'bg-blue-600 text-white'
                  : 'bg-white/10 text-white/60 hover:bg-white/20'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Papers List */}
      <div className="space-y-4">
        {filteredPapers.map((paper, index) => (
          <div
            key={paper.id || `paper-${index}`}
            className="bg-black/20 backdrop-blur-sm border border-white/10 rounded-xl p-6 hover:border-blue-500/30 transition-all duration-300 group"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 bg-blue-600/20 text-blue-400 text-xs rounded">
                    {paper.category}
                  </span>
                  <span className="text-xs text-white/40">
                    {new Date(paper.published).toLocaleDateString('en-US', { 
                      month: 'short', 
                      day: 'numeric', 
                      year: 'numeric' 
                    })}
                  </span>
                </div>
                
                <h3 className="text-lg font-semibold text-white mb-2 group-hover:text-blue-400 transition-colors">
                  {paper.title}
                </h3>
                
                <p className="text-sm text-white/50 mb-3">
                  {paper.authors}
                </p>
                
                {paper.summary && (
                  <p className="text-sm text-white/70 leading-relaxed mb-3">
                    {paper.summary}
                  </p>
                )}
                
                <a
                  href={paper.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm text-blue-400 hover:text-blue-300 transition-colors"
                >
                  Read paper
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

