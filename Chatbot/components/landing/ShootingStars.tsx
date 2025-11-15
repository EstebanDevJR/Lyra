'use client'

import { useEffect, useRef } from 'react'

export default function ShootingStars() {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const createShootingStar = () => {
      const star = document.createElement('div')
      star.className = 'shooting-star'
      
      // Posición inicial aleatoria desde la parte superior
      const startX = Math.random() * window.innerWidth
      const startY = -10
      
      // Dirección aleatoria hacia abajo
      const angle = Math.random() * 60 - 30 // Entre -30 y 30 grados
      const distance = window.innerHeight + 200
      const endX = startX + Math.sin((angle * Math.PI) / 180) * distance
      const endY = startY + Math.cos((angle * Math.PI) / 180) * distance
      
      // Duración aleatoria entre 1.5s y 3s
      const duration = 1.5 + Math.random() * 1.5
      
      // Tamaño aleatorio
      const size = 2 + Math.random() * 2
      
      star.style.left = `${startX}px`
      star.style.top = `${startY}px`
      star.style.width = `${size}px`
      star.style.height = `${size}px`
      star.style.animationDuration = `${duration}s`
      star.style.opacity = `${0.6 + Math.random() * 0.4}`
      
      container.appendChild(star)
      
      // Animar la estrella
      star.animate([
        { 
          transform: `translate(0, 0) rotate(${angle}deg)`,
          opacity: 0
        },
        { 
          transform: `translate(${endX - startX}px, ${endY - startY}px) rotate(${angle}deg)`,
          opacity: 1,
          offset: 0.1
        },
        { 
          transform: `translate(${endX - startX}px, ${endY - startY}px) rotate(${angle}deg)`,
          opacity: 0.8,
          offset: 0.9
        },
        { 
          transform: `translate(${endX - startX}px, ${endY - startY}px) rotate(${angle}deg)`,
          opacity: 0
        }
      ], {
        duration: duration * 1000,
        easing: 'linear'
      }).onfinish = () => {
        star.remove()
      }
    }

    // Crear estrellas periódicamente
    const interval = setInterval(() => {
      createShootingStar()
    }, 2000 + Math.random() * 3000) // Cada 2-5 segundos

    // Crear algunas estrellas iniciales
    for (let i = 0; i < 3; i++) {
      setTimeout(() => createShootingStar(), i * 1000)
    }

    return () => {
      clearInterval(interval)
    }
  }, [])

  return (
    <div 
      ref={containerRef}
      className="shooting-stars-container"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 2,
        overflow: 'hidden'
      }}
    />
  )
}

