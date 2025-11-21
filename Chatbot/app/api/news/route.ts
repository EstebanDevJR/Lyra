import { NextResponse } from 'next/server';

export async function GET() {
  // URL del webhook de n8n (puede ser variable de entorno)
  let N8N_URL = process.env.NEXT_PUBLIC_N8N_NEWS_WEBHOOK;

  // Fix for localhost connectivity issues in Node.js environments
  // Node often prefers IPv6 (::1) for localhost, but some servers listen on IPv4 (127.0.0.1)
  if (N8N_URL && N8N_URL.includes('localhost')) {
    N8N_URL = N8N_URL.replace('localhost', '127.0.0.1');
  }

  console.log('News Proxy: Attempting to fetch from', N8N_URL);

  if (!N8N_URL) {
    console.error('News Proxy Error: N8N_URL not configured');
    return NextResponse.json(
      { error: 'N8N_URL not configured' },
      { status: 500 }
    );
  }

  try {
    // Llamada backend-to-backend (sin CORS)
    const response = await fetch(N8N_URL, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // next: { revalidate: 3600 } // Opcional: Cache por 1 hora
    });

    console.log('News Proxy: N8N response status', response.status);

    if (!response.ok) {
      const text = await response.text();
      console.error('News Proxy Error: N8N responded with error', response.status, text);
      throw new Error(`N8N responded with ${response.status}: ${text}`);
    }

    const data = await response.json();
    
    // Debug logging
    console.log('News Proxy: Data type received:', Array.isArray(data) ? 'Array' : typeof data);
    console.log('News Proxy: Data length/keys:', Array.isArray(data) ? data.length : Object.keys(data).length);
    console.log('News Proxy: First item preview:', Array.isArray(data) ? data[0] : data);
    
    // Ensure we always return an array
    const newsArray = Array.isArray(data) ? data : [data];
    
    return NextResponse.json(newsArray);
  } catch (error) {
    console.error('Error proxying to n8n:', error);
    return NextResponse.json(
      { error: 'Failed to fetch news', details: String(error) },
      { status: 500 }
    );
  }
}

