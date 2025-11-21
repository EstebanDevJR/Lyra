'use client'

import { useRef, useState, MouseEvent } from 'react'

interface Card3DProps {
  children: React.ReactNode
  className?: string
  delay?: string
}

export default function Card3D({ children, className = '', delay = '0s' }: Card3DProps) {
  const cardRef = useRef<HTMLDivElement>(null)
  const [transform, setTransform] = useState('')
  const [shineOpacity, setShineOpacity] = useState(0)
  const [shinePos, setShinePos] = useState({ x: 0, y: 0 })

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return

    const card = cardRef.current
    const rect = card.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    
    const centerX = rect.width / 2
    const centerY = rect.height / 2
    
    const rotateX = ((y - centerY) / centerY) * -5 // Max rotation deg
    const rotateY = ((x - centerX) / centerX) * 5

    setTransform(`perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`)
    
    // Shine effect
    setShineOpacity(1)
    setShinePos({ x, y })
  }

  const handleMouseLeave = () => {
    setTransform('perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)')
    setShineOpacity(0)
  }

  return (
    <div 
      className={`fade-in-up ${className}`}
      style={{ animationDelay: delay, perspective: '1000px' }}
    >
      <div
        ref={cardRef}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={{
          transform,
          transition: 'transform 0.1s ease-out',
          willChange: 'transform',
        }}
        className="relative bg-black/40 backdrop-blur-xl border border-white/10 rounded-xl overflow-hidden group"
      >
        {/* Content - using CSS class for reliable padding */}
        <div className="relative z-10 card-3d-content">
          {children}
        </div>

        {/* Shine Effect */}
        <div 
          className="absolute pointer-events-none z-20 inset-0"
          style={{
            background: `radial-gradient(circle at ${shinePos.x}px ${shinePos.y}px, rgba(255,255,255,0.15) 0%, transparent 50%)`,
            opacity: shineOpacity,
            transition: 'opacity 0.3s ease',
          }}
        />

        {/* Border Gradient Animation */}
        <div className="absolute inset-0 z-0 opacity-50 group-hover:opacity-100 transition-opacity duration-500">
            <div className="absolute inset-[-50%] bg-[conic-gradient(from_0deg,transparent_0_340deg,white_360deg)] animate-[spin_4s_linear_infinite] w-[200%] h-[200%] opacity-20" />
        </div>
        
        {/* Inner Background */}
        <div className="absolute inset-px bg-[#050508] rounded-xl z-0" />
      </div>
    </div>
  )
}
