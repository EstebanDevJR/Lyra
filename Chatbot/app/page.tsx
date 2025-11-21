'use client'

import dynamic from 'next/dynamic'
import { useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import './landing.css'
import InfoHero from '@/components/landing/InfoHero'
import AboutSection from '@/components/landing/AboutSection'
import TechnologiesSection from '@/components/landing/TechnologiesSection'
import HowItWorksSection from '@/components/landing/HowItWorksSection'
import ProcessSteps from '@/components/landing/ProcessSteps'
import ArchitectureSection from '@/components/landing/ArchitectureSection'
import ShootingStars from '@/components/landing/ShootingStars'
import Footer from '@/components/landing/Footer'

import Card3D from '@/components/landing/Card3D'
import ThreeBackground from '@/components/landing/ThreeBackground'

// Dynamic import para evitar SSR de Three.js
const ThreeScene = dynamic(() => import('@/components/three-scene'), {
  ssr: false,
  loading: () => (
    <div className="canvas-container">
      <div style={{ 
        position: 'absolute', 
        top: '50%', 
        left: '50%', 
        transform: 'translate(-50%, -50%)',
        color: 'white',
        fontSize: '18px'
      }}>
        Cargando...
      </div>
    </div>
  )
})

export default function HomePage() {
  const router = useRouter()
  const canvasContainerRef = useRef<HTMLDivElement>(null)

  const handleStartConversation = () => {
    // Usar window.location.href para hacer un refresh completo de la página de chat
    window.location.href = '/chat'
  }

  return (
    <>
      <div className="canvas-container" id="canvas-container" ref={canvasContainerRef}>
        {/* Title and GitHub Button */}
        <h1 className="lyra-title">Lyra</h1>
        <a 
          href="https://github.com/EstebanDevJR/Lyra.git" 
          target="_blank" 
          rel="noopener noreferrer" 
          className="github-button"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
          </svg>
          GitHub
        </a>
        
        {/* 360 View Indicator */}
        <div className="view-360-indicator">
          <div className="indicator-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
              <circle cx="12" cy="12" r="3"></circle>
            </svg>
          </div>
          <span className="indicator-text">360°</span>
          <span className="indicator-hint">Arrastra para rotar</span>
        </div>
        
        {/* Scroll Down Arrow */}
        <div className="scroll-down-arrow">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 5v14M5 12l7 7 7-7"></path>
          </svg>
        </div>
        
        {/* Three.js Canvas - loaded dynamically */}
        <ThreeScene onStartConversation={handleStartConversation} />
      </div>

      {/* Shooting Stars Animation */}
      <ShootingStars />

      {/* Information Section */}
      <section className="info-section relative overflow-hidden">
        <ThreeBackground />
        
        <div className="info-content relative z-10">
          {/* Hero Section */}
          <InfoHero />

          {/* Separated Cards */}
          <Card3D delay="0.2s">
            <AboutSection />
          </Card3D>

          <Card3D delay="0.3s">
            <TechnologiesSection />
          </Card3D>

          <Card3D delay="0.4s">
            <HowItWorksSection />
          </Card3D>

          <Card3D delay="0.5s">
            <ProcessSteps />
          </Card3D>

          <Card3D delay="0.6s">
            <ArchitectureSection />
          </Card3D>
        </div>
      </section>

      {/* Footer */}
      <Footer />
    </>
  )
}
