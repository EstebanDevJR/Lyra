import { NextResponse } from 'next/server';

export async function GET() {
  const N8N_URL = process.env.NEXT_PUBLIC_N8N_ASTRONOMY_IMAGE_WEBHOOK;

  console.log('Astronomy Image API: N8N_URL configured?', !!N8N_URL);
  console.log('Astronomy Image API: N8N_URL value:', N8N_URL ? '***configured***' : 'NOT SET');

  if (!N8N_URL) {
    console.log('Astronomy Image API: N8N_URL not configured, using NASA APOD fallback');
    // Fallback to NASA APOD API if n8n not configured
    const NASA_API_KEY = process.env.NASA_API_KEY || 'DEMO_KEY';
    const NASA_URL = `https://api.nasa.gov/planetary/apod?api_key=${NASA_API_KEY}`;
    
    try {
      const response = await fetch(NASA_URL);
      if (!response.ok) throw new Error(`NASA API error: ${response.status}`);
      
      const data = await response.json();
      console.log('Astronomy Image API: Successfully fetched from NASA APOD');
      return NextResponse.json(data);
    } catch (error) {
      console.error('Astronomy Image API: Error fetching from NASA APOD:', error);
      return NextResponse.json(
        { error: 'Failed to fetch astronomy image' },
        { status: 500 }
      );
    }
  }

  // Use n8n webhook if configured
  // Fix common URL issues
  let fixedURL = N8N_URL;
  if (fixedURL.includes('localhost')) {
    fixedURL = fixedURL.replace('localhost', '127.0.0.1');
  }
  
  // Ensure proper path separator (fix "5678webhook" -> "5678/webhook")
  fixedURL = fixedURL.replace(/(\d)(webhook)/, '$1/$2');
  
  // Asegurar que la URL tenga /webhook/ en la ruta
  // Si la URL es http://127.0.0.1:5678/astronomy-image, cambiarla a http://127.0.0.1:5678/webhook/astronomy-image
  try {
    const url = new URL(fixedURL);
    const pathname = url.pathname;
    
    // Si el pathname no contiene /webhook/, agregarlo
    if (!pathname.includes('/webhook/')) {
      // Extraer el nombre del webhook (último segmento del path)
      const webhookName = pathname.split('/').filter(p => p).pop() || 'astronomy-image';
      // Reconstruir la URL con /webhook/ en el path
      url.pathname = `/webhook/${webhookName}`;
      fixedURL = url.toString();
    }
  } catch (e) {
    // Si falla el parsing de URL, intentar con regex simple
    if (!fixedURL.includes('/webhook/')) {
      fixedURL = fixedURL.replace(/:(\d+)\/([^\/\s]+)$/, ':$1/webhook/$2');
    }
  }
  
  console.log('Astronomy Image API: Fetching from', fixedURL);
  
  try {
    const response = await fetch(fixedURL, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.warn(`Astronomy Image API: N8N responded with ${response.status}`);
      console.warn(`Astronomy Image API: Response preview:`, errorText.substring(0, 200));
      // Fallback to NASA APOD
      const NASA_API_KEY = process.env.NASA_API_KEY || 'DEMO_KEY';
      const NASA_URL = `https://api.nasa.gov/planetary/apod?api_key=${NASA_API_KEY}`;
      const nasaResponse = await fetch(NASA_URL);
      if (nasaResponse.ok) {
        const nasaData = await nasaResponse.json();
        return NextResponse.json(nasaData);
      }
      throw new Error(`Both N8N and NASA APOD failed`);
    }

    // Verificar que la respuesta sea JSON, no HTML
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      const textResponse = await response.text();
      console.error('Astronomy Image API: N8N returned non-JSON response (likely HTML)');
      console.error('Astronomy Image API: Content-Type:', contentType);
      console.error('Astronomy Image API: Response preview:', textResponse.substring(0, 300));
      throw new Error('N8N returned HTML instead of JSON. Check webhook URL and workflow configuration.');
    }

    const data = await response.json();
    console.log('Astronomy Image API: N8N response received, data type:', Array.isArray(data) ? 'Array' : typeof data);
    console.log('Astronomy Image API: N8N response structure:', JSON.stringify(data).substring(0, 200));
    
    // n8n puede devolver un array con un objeto dentro: [{...}]
    // o un objeto directo: {...}
    let imageData = data;
    
    if (Array.isArray(data) && data.length > 0) {
      // Si es un array, tomar el primer elemento
      imageData = data[0];
      console.log('Astronomy Image API: Extracted from array, title:', imageData?.title);
    } else if (data && data.data && Array.isArray(data.data) && data.data.length > 0) {
      // Si es { data: [{...}] }
      imageData = data.data[0];
      console.log('Astronomy Image API: Extracted from data.data, title:', imageData?.title);
    }
    
    // Validar que tenemos los campos necesarios
    if (imageData && imageData.title) {
      console.log('Astronomy Image API: Successfully returning n8n data:', imageData.title);
      return NextResponse.json(imageData);
    } else {
      console.warn('Astronomy Image API: Invalid data structure from n8n, falling back to NASA APOD');
      console.warn('Astronomy Image API: imageData:', imageData);
      // Fallback to NASA APOD
      const NASA_API_KEY = process.env.NASA_API_KEY || 'DEMO_KEY';
      const NASA_URL = `https://api.nasa.gov/planetary/apod?api_key=${NASA_API_KEY}`;
      const nasaResponse = await fetch(NASA_URL);
      if (nasaResponse.ok) {
        const nasaData = await nasaResponse.json();
        console.log('Astronomy Image API: Using NASA APOD as fallback');
        return NextResponse.json(nasaData);
      }
      throw new Error('Invalid data from n8n and NASA APOD fallback failed');
    }
  } catch (error) {
    console.error('Astronomy Image API: Error proxying to n8n:', error);
    console.error('Astronomy Image API: Error details:', error instanceof Error ? error.message : String(error));
    // Try NASA APOD as final fallback
    try {
      const NASA_API_KEY = process.env.NASA_API_KEY || 'DEMO_KEY';
      const NASA_URL = `https://api.nasa.gov/planetary/apod?api_key=${NASA_API_KEY}`;
      console.log('Astronomy Image API: Attempting NASA APOD fallback...');
      const nasaResponse = await fetch(NASA_URL);
      if (nasaResponse.ok) {
        const nasaData = await nasaResponse.json();
        console.log('Astronomy Image API: Successfully using NASA APOD as fallback');
        return NextResponse.json(nasaData);
      } else {
        console.error('Astronomy Image API: NASA APOD responded with status:', nasaResponse.status);
      }
    } catch (nasaError) {
      console.error('Astronomy Image API: Error fetching from NASA APOD:', nasaError);
    }
    
    // Last resort: return fallback data structure
    console.warn('Astronomy Image API: All fallbacks failed, using hardcoded fallback');
    return NextResponse.json({
      title: 'The Pillars of Creation',
      explanation: 'The iconic Pillars of Creation captured by the James Webb Space Telescope, revealing new details of star formation.',
      url: 'https://images.unsplash.com/photo-1462331940025-496dfbfc7564?q=80&w=800&auto=format&fit=crop',
      date: new Date().toISOString().split('T')[0],
      media_type: 'image'
    });
  }
}

