import { NextResponse } from 'next/server';

// Fallback data matching the component's FALLBACK_PAPERS structure
const FALLBACK_PAPERS = [
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
];

export async function GET() {
  let N8N_URL = process.env.NEXT_PUBLIC_N8N_RESEARCH_PAPERS_WEBHOOK;

  if (!N8N_URL) {
    console.log('Research Papers API: N8N_URL not configured, using fallback data');
    return NextResponse.json(FALLBACK_PAPERS);
  }

  // Fix common URL issues
  if (N8N_URL.includes('localhost')) {
    N8N_URL = N8N_URL.replace('localhost', '127.0.0.1');
  }
  
  // Ensure proper path separator (fix "5678webhook" -> "5678/webhook")
  N8N_URL = N8N_URL.replace(/(\d)(webhook)/, '$1/$2');
  
  console.log('Research Papers API: Fetching from', N8N_URL);

  try {
    const response = await fetch(N8N_URL, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      console.warn(`Research Papers API: N8N responded with ${response.status}, using fallback`);
      return NextResponse.json(FALLBACK_PAPERS);
    }

    const data = await response.json();
    
    console.log('Research Papers: Raw data type:', Array.isArray(data) ? 'Array' : typeof data);
    console.log('Research Papers: Raw data structure:', JSON.stringify(data).substring(0, 200));
    
    // n8n puede devolver datos en diferentes estructuras:
    // 1. Array directo: [{...}, {...}]
    // 2. Objeto con data: { data: [{...}, {...}] }
    // 3. Array con objeto que tiene data: [{ data: [{...}, {...}] }]
    // 4. Array con objetos individuales: [{ json: {...} }, { json: {...} }]
    
    let papersArray = [];
    
    if (Array.isArray(data)) {
      // Si es un array, verificar su estructura
      if (data.length > 0) {
        const firstItem = data[0];
        
        // Caso: [{ data: [...] }]
        if (firstItem && firstItem.data && Array.isArray(firstItem.data)) {
          papersArray = firstItem.data;
        }
        // Caso: [{ json: {...} }, { json: {...} }]
        else if (firstItem && firstItem.json) {
          papersArray = data.map(item => item.json);
        }
        // Caso: Array directo de papers
        else if (firstItem && (firstItem.id || firstItem.title || firstItem.summary)) {
          papersArray = data;
        }
      }
    } 
    // Caso: { data: [...] }
    else if (data && data.data && Array.isArray(data.data)) {
      papersArray = data.data;
    }
    // Caso: Objeto único que es un paper
    else if (data && (data.id || data.title || data.summary)) {
      papersArray = [data];
    }
    
    console.log('Research Papers: Extracted papers count:', papersArray.length);
    
    // Validar que tenemos papers válidos (al menos con summary o title)
    const validPapers = papersArray.filter(paper => 
      paper && (paper.title || paper.summary || paper.abstract)
    );
    
    if (validPapers.length > 0) {
      return NextResponse.json(validPapers);
    } else {
      console.warn('Research Papers API: No valid papers found in response, using fallback');
      return NextResponse.json(FALLBACK_PAPERS);
    }
  } catch (error) {
    console.error('Error proxying to n8n:', error);
    console.log('Research Papers API: Using fallback data due to error');
    return NextResponse.json(FALLBACK_PAPERS);
  }
}

