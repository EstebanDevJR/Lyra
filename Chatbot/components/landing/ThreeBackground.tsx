'use client'

import { useEffect, useRef } from 'react'
import * as THREE from 'three'

export default function ThreeBackground() {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!containerRef.current) return

    // Scene Setup
    const scene = new THREE.Scene()
    // Fog for depth fading
    scene.fog = new THREE.FogExp2(0x020205, 0.002)

    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
    camera.position.z = 50

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
    renderer.setSize(window.innerWidth, window.innerHeight)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    containerRef.current.appendChild(renderer.domElement)

    // GEOMETRY: Floating Particles / Network
    const geometry = new THREE.BufferGeometry()
    const count = 1000
    const posArray = new Float32Array(count * 3)
    
    for(let i = 0; i < count * 3; i++) {
      posArray[i] = (Math.random() - 0.5) * 100
    }
    
    geometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3))

    // Create custom shader material for glowing points
    const material = new THREE.PointsMaterial({
      size: 0.15,
      color: 0xFFFFFF, // Electric Blue
      transparent: true,
      opacity: 1,
      blending: THREE.AdditiveBlending
    })

    const particlesMesh = new THREE.Points(geometry, material)
    scene.add(particlesMesh)

    // Connect nearby particles with lines
    const lineMaterial = new THREE.LineBasicMaterial({
      color: 0xbc13fe, // Neon Purple
      transparent: true,
      opacity: 0.15
    })
    
    // We will create a subset of lines dynamically in animation loop or static mesh
    // For performance, let's use a static wireframe object rotating
    const icosahedronGeometry = new THREE.IcosahedronGeometry(30, 1)
    const wireframe = new THREE.WireframeGeometry(icosahedronGeometry)
    const lineSegments = new THREE.LineSegments(wireframe, lineMaterial)
    scene.add(lineSegments)


    // Animation Loop
    let animationFrameId: number

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate)

      // Rotate entire system slowly
      particlesMesh.rotation.y += 0.0005
      particlesMesh.rotation.x += 0.0002
      
      lineSegments.rotation.y -= 0.001
      lineSegments.rotation.x -= 0.0005

      // Mouse interaction could be added here by tracking mouse pos

      renderer.render(scene, camera)
    }

    animate()

    // Resize Handler
    const handleResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight
      camera.updateProjectionMatrix()
      renderer.setSize(window.innerWidth, window.innerHeight)
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      cancelAnimationFrame(animationFrameId)
      if (containerRef.current) {
        containerRef.current.removeChild(renderer.domElement)
      }
      geometry.dispose()
      material.dispose()
      renderer.dispose()
    }
  }, [])

  return (
    <div 
      ref={containerRef} 
      className="absolute inset-0 z-0 pointer-events-none"
      style={{ opacity: 0.6 }} // Subtle background
    />
  )
}

