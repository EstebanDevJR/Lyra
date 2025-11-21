import { NextResponse } from 'next/server';

// Fallback data matching the component's FALLBACK_ALERTS structure
const FALLBACK_ALERTS = [
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
];

export async function GET() {
  let N8N_URL = process.env.NEXT_PUBLIC_N8N_ASTRO_ALERTS_WEBHOOK;

  if (!N8N_URL) {
    console.log('Astro Alerts API: N8N_URL not configured, using fallback data');
    return NextResponse.json(FALLBACK_ALERTS);
  }

  // Fix common URL issues
  if (N8N_URL.includes('localhost')) {
    N8N_URL = N8N_URL.replace('localhost', '127.0.0.1');
  }
  
  // Ensure proper path separator (fix "5678webhook" -> "5678/webhook")
  N8N_URL = N8N_URL.replace(/(\d)(webhook)/, '$1/$2');
  
  console.log('Astro Alerts API: Fetching from', N8N_URL);

  try {
    const response = await fetch(N8N_URL, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      console.warn(`Astro Alerts API: N8N responded with ${response.status}, using fallback`);
      return NextResponse.json(FALLBACK_ALERTS);
    }

    const data = await response.json();
    
    console.log('Astro Alerts: Data type:', Array.isArray(data) ? 'Array' : typeof data);
    console.log('Astro Alerts: Count:', Array.isArray(data) ? data.length : 'N/A');
    
    // Ensure we always return an array
    const alertsArray = Array.isArray(data) && data.length > 0 ? data : FALLBACK_ALERTS;
    
    return NextResponse.json(alertsArray);
  } catch (error) {
    console.error('Error proxying to n8n:', error);
    console.log('Astro Alerts API: Using fallback data due to error');
    return NextResponse.json(FALLBACK_ALERTS);
  }
}

