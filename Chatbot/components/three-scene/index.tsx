'use client'

import { useEffect, useRef, useState } from 'react'
import dynamic from 'next/dynamic'

interface ThreeSceneProps {
  onStartConversation: () => void
}

// Componente que carga Three.js dinámicamente
export default function ThreeScene({ onStartConversation }: ThreeSceneProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const experienceRef = useRef<any>(null)
  const originalCameraPositionRef = useRef<{ x: number; y: number; z: number } | null>(null)
  const originalCameraTargetRef = useRef<{ x: number; y: number; z: number } | null>(null)
  const originalControlsSettingsRef = useRef<any>(null)
  const [isZooming, setIsZooming] = useState(false)
  const [buttonText, setButtonText] = useState('Iniciar Conversación')
  const [isReady, setIsReady] = useState(false)

  // Restaurar posición de cámara cuando el componente se monta
  useEffect(() => {
    const restoreCameraPosition = async () => {
      if (!experienceRef.current) return
      
      const experience = experienceRef.current
      const camera = experience.mainCamera?.instance || experience.worlds?.mainWorld?.camera?.instance
      const controls = experience.mainCamera?.controls || experience.worlds?.mainWorld?.camera?.controls
      
      if (!camera) return
      
      // Posición por defecto de la cámara (según Camera.js: new THREE.Vector3(1, 0.5, 3))
      const defaultPosition = { x: 1, y: 0.5, z: 3 }
      const defaultTarget = { x: 0, y: 0, z: 0 }
      
      // Verificar si la cámara está en posición de zoom (muy cerca del origen)
      const distanceFromOrigin = Math.sqrt(
        camera.position.x ** 2 + 
        camera.position.y ** 2 + 
        camera.position.z ** 2
      )
      
      // Si está muy cerca del origen (menos de 1 unidad), probablemente está en zoom
      const isZoomed = distanceFromOrigin < 1.0
      
      // Si no tenemos la posición original guardada, usar la posición por defecto
      if (!originalCameraPositionRef.current) {
        // Si está en zoom, restaurar inmediatamente a la posición por defecto
        if (isZoomed) {
          const THREE = await import('three')
          const gsap = (await import('gsap')).default
          
          // Restaurar posición de la cámara a la posición por defecto
          gsap.to(camera.position, {
            x: defaultPosition.x,
            y: defaultPosition.y,
            z: defaultPosition.z,
            duration: 1.5,
            ease: "power2.out"
          })
          
          // Restaurar target y configuración de controles
          if (controls) {
            gsap.to(controls.target, {
              x: defaultTarget.x,
              y: defaultTarget.y,
              z: defaultTarget.z,
              duration: 1.5,
              ease: "power2.out",
              onComplete: () => {
                // Restaurar configuración de controles a valores por defecto
                const fixedDistance = Math.sqrt(defaultPosition.x ** 2 + defaultPosition.y ** 2 + defaultPosition.z ** 2)
                controls.minDistance = fixedDistance
                controls.maxDistance = fixedDistance
                controls.enableZoom = false
                controls.enabled = true
                controls.update()
              }
            })
          }
          
          setIsZooming(false)
          setButtonText('Iniciar Conversación')
        } else {
          // Guardar la posición actual como original si no está en zoom
          originalCameraPositionRef.current = {
            x: camera.position.x,
            y: camera.position.y,
            z: camera.position.z
          }
          
          if (controls && controls.target) {
            originalCameraTargetRef.current = {
              x: controls.target.x,
              y: controls.target.y,
              z: controls.target.z
            }
            originalControlsSettingsRef.current = {
              minDistance: controls.minDistance,
              maxDistance: controls.maxDistance,
              enableZoom: controls.enableZoom !== undefined ? controls.enableZoom : true,
              enabled: controls.enabled
            }
          }
        }
        return
      }
      
      // Si tenemos la posición original guardada y está en zoom, restaurar
      if (isZoomed && originalCameraPositionRef.current) {
        const THREE = await import('three')
        const gsap = (await import('gsap')).default
        
        // Restaurar posición de la cámara
        gsap.to(camera.position, {
          x: originalCameraPositionRef.current.x,
          y: originalCameraPositionRef.current.y,
          z: originalCameraPositionRef.current.z,
          duration: 1.5,
          ease: "power2.out"
        })
        
        // Restaurar target y configuración de controles
        if (controls && originalCameraTargetRef.current && originalControlsSettingsRef.current) {
          gsap.to(controls.target, {
            x: originalCameraTargetRef.current.x,
            y: originalCameraTargetRef.current.y,
            z: originalCameraTargetRef.current.z,
            duration: 1.5,
            ease: "power2.out",
            onComplete: () => {
              controls.minDistance = originalControlsSettingsRef.current.minDistance
              controls.maxDistance = originalControlsSettingsRef.current.maxDistance
              controls.enableZoom = originalControlsSettingsRef.current.enableZoom
              controls.enabled = originalControlsSettingsRef.current.enabled
              controls.update()
            }
          })
        } else if (controls) {
          controls.update()
        }
        
        setIsZooming(false)
        setButtonText('Iniciar Conversación')
      }
    }
    
    // Esperar a que el componente esté listo antes de restaurar
    if (isReady) {
      // Ejecutar inmediatamente y también después de delays para asegurar que se ejecute
      restoreCameraPosition()
      setTimeout(restoreCameraPosition, 300)
      setTimeout(restoreCameraPosition, 800)
      setTimeout(restoreCameraPosition, 1500)
      setTimeout(restoreCameraPosition, 2500)
    }
  }, [isReady])
  
  // También restaurar cuando la página se vuelve visible (útil para navegación hacia atrás)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && isReady) {
        setTimeout(() => {
          const restoreCameraPosition = async () => {
            if (!experienceRef.current) return
            
            const experience = experienceRef.current
            const camera = experience.mainCamera?.instance || experience.worlds?.mainWorld?.camera?.instance
            const controls = experience.mainCamera?.controls || experience.worlds?.mainWorld?.camera?.controls
            
            if (!camera) return
            
            const defaultPosition = { x: 1, y: 0.5, z: 3 }
            const defaultTarget = { x: 0, y: 0, z: 0 }
            
            const distanceFromOrigin = Math.sqrt(
              camera.position.x ** 2 + 
              camera.position.y ** 2 + 
              camera.position.z ** 2
            )
            
            const isZoomed = distanceFromOrigin < 1.0
            
            if (isZoomed) {
              const THREE = await import('three')
              const gsap = (await import('gsap')).default
              
              gsap.to(camera.position, {
                x: defaultPosition.x,
                y: defaultPosition.y,
                z: defaultPosition.z,
                duration: 1.5,
                ease: "power2.out"
              })
              
              if (controls) {
                gsap.to(controls.target, {
                  x: defaultTarget.x,
                  y: defaultTarget.y,
                  z: defaultTarget.z,
                  duration: 1.5,
                  ease: "power2.out",
                  onComplete: () => {
                    const fixedDistance = Math.sqrt(defaultPosition.x ** 2 + defaultPosition.y ** 2 + defaultPosition.z ** 2)
                    controls.minDistance = fixedDistance
                    controls.maxDistance = fixedDistance
                    controls.enableZoom = false
                    controls.enabled = true
                    controls.update()
                  }
                })
              }
            }
          }
          restoreCameraPosition()
        }, 100)
      }
    }
    
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [isReady])

  useEffect(() => {
    if (!canvasRef.current) return

    // Dynamic import de Experience completo
    const initExperience = async () => {
      try {
        // Importar Experience dinámicamente
        const ExperienceModule = await import('@/lib/experience/Experience.js')
        const Experience = ExperienceModule.default
        
        // Verificar si ya existe una instancia y si la cámara está en zoom
        const existingInstance = (window as any).experience
        if (existingInstance) {
          const existingCamera = existingInstance.mainCamera?.instance || existingInstance.worlds?.mainWorld?.camera?.instance
          if (existingCamera) {
            const distanceFromOrigin = Math.sqrt(
              existingCamera.position.x ** 2 + 
              existingCamera.position.y ** 2 + 
              existingCamera.position.z ** 2
            )
            
            // Si está en zoom, destruir la instancia anterior para forzar recreación
            if (distanceFromOrigin < 1.0) {
              try {
                if (typeof existingInstance.destroy === 'function') {
                  existingInstance.destroy()
                }
                // Limpiar la instancia singleton
                Experience._instance = null
                ;(window as any).experience = null
              } catch (e) {
                console.warn('Error destroying existing instance:', e)
              }
            }
          }
        }
        
        // Crear instancia de Experience
        const experience = new Experience(canvasRef.current!)
        experienceRef.current = experience

        setIsReady(true)
        
        // Guardar posición original de la cámara cuando esté lista
        setTimeout(() => {
          const camera = experience.mainCamera?.instance || experience.worlds?.mainWorld?.camera?.instance
          const controls = experience.mainCamera?.controls || experience.worlds?.mainWorld?.camera?.controls
          
          if (camera) {
            originalCameraPositionRef.current = {
              x: camera.position.x,
              y: camera.position.y,
              z: camera.position.z
            }
          }
          
          if (controls && controls.target) {
            originalCameraTargetRef.current = {
              x: controls.target.x,
              y: controls.target.y,
              z: controls.target.z
            }
            originalControlsSettingsRef.current = {
              minDistance: controls.minDistance,
              maxDistance: controls.maxDistance,
              enableZoom: controls.enableZoom !== undefined ? controls.enableZoom : true,
              enabled: controls.enabled
            }
          }
          
          window.dispatchEvent(new Event('3d-app:classes-ready'))
        }, 500)
      } catch (error) {
        console.error('Error loading Experience:', error)
        // Fallback: crear una escena básica de Three.js
        const THREE = await import('three')
        const scene = new THREE.Scene()
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
        const renderer = new THREE.WebGLRenderer({ 
          canvas: canvasRef.current!,
          antialias: true,
          alpha: true
        })
        renderer.setSize(window.innerWidth, window.innerHeight)
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
        camera.position.z = 5
        
        experienceRef.current = {
          scene,
          camera,
          renderer,
          mainCamera: {
            instance: camera,
            controls: null
          }
        }
        
        const animate = () => {
          requestAnimationFrame(animate)
          renderer.render(scene, camera)
        }
        animate()
        setIsReady(true)
      }
    }

    initExperience()

    return () => {
      // Cleanup
      if (experienceRef.current) {
        try {
          if (typeof experienceRef.current.destroy === 'function') {
            experienceRef.current.destroy()
          } else if (experienceRef.current.renderer?.instance?.dispose) {
            experienceRef.current.renderer.instance.dispose()
          }
        } catch (error) {
          console.warn('Error during cleanup:', error)
        }
        experienceRef.current = null
      }
    }
  }, [])

  const handleZoomClick = async () => {
    if (isZooming || !isReady) return

    setIsZooming(true)
    setButtonText('Iniciando...')

    // Importar GSAP y THREE dinámicamente
    const gsap = (await import('gsap')).default
    const THREE = await import('three')

    const experience = experienceRef.current
    if (!experience) {
      console.warn('Experience not ready')
      setIsZooming(false)
      setButtonText('Iniciar Conversación')
      return
    }

    // Intentar obtener la cámara de diferentes formas
    let camera = null
    let controls = null
    
    if (experience.mainCamera) {
      camera = experience.mainCamera.instance
      controls = experience.mainCamera.controls
    } else if (experience.worlds?.mainWorld?.camera) {
      camera = experience.worlds.mainWorld.camera.instance
      controls = experience.worlds.mainWorld.camera.controls
    } else if (experience.camera) {
      camera = experience.camera
    }
    
    if (!camera) {
      console.warn('Camera not available yet')
      setIsZooming(false)
      setButtonText('Iniciar Conversación')
      return
    }

    // Guardar posición original
    const originalCameraPosition = camera.position.clone()
    const originalCameraTarget = controls ? controls.target.clone() : new THREE.Vector3(0, 0, 0)

    // Calcular dirección hacia el centro del agujero negro
    const blackHoleCenter = new THREE.Vector3(0, 0, 0)
    const directionToCenter = blackHoleCenter.clone().sub(camera.position).normalize()
    
    // Posición muy cerca del centro
    const zoomDistance = 0.1
    const zoomPosition = blackHoleCenter.clone().sub(directionToCenter.multiplyScalar(zoomDistance))
    const zoomTarget = new THREE.Vector3(0, 0, 0)

    // Permitir que la distancia cambie durante la animación si hay controls
    if (controls) {
      const originalMinDistance = controls.minDistance
      const originalMaxDistance = controls.maxDistance
      controls.minDistance = 0
      controls.maxDistance = 1000
      controls.enabled = false
    }

    // Animación de zoom
    gsap.to(camera.position, {
      x: zoomPosition.x,
      y: zoomPosition.y,
      z: zoomPosition.z,
      duration: 2.5,
      ease: "power2.inOut",
      onUpdate: () => {
        camera.lookAt(zoomTarget)
        if (controls) {
          controls.update()
        }
      },
      onComplete: () => {
        camera.lookAt(zoomTarget)
        if (controls) {
          controls.update()
          controls.minDistance = zoomDistance
          controls.maxDistance = zoomDistance
          controls.enableZoom = false
          controls.enabled = true
        }
        setTimeout(() => {
          onStartConversation()
        }, 1000)
      }
    })

    if (controls) {
      gsap.to(controls.target, {
        x: zoomTarget.x,
        y: zoomTarget.y,
        z: zoomTarget.z,
        duration: 2.5,
        ease: "power2.inOut"
      })
    }
  }

  // Setup scroll indicators hiding
  useEffect(() => {
    const view360Indicator = document.querySelector('.view-360-indicator')
    const scrollDownArrow = document.querySelector('.scroll-down-arrow')
    let hasScrolled = false

    const hideIndicators = () => {
      if (!hasScrolled) {
        hasScrolled = true
        if (view360Indicator) {
          view360Indicator.classList.add('hidden')
          setTimeout(() => {
            if (view360Indicator) {
              (view360Indicator as HTMLElement).style.display = 'none'
            }
          }, 500)
        }
        if (scrollDownArrow) {
          scrollDownArrow.classList.add('hidden')
          setTimeout(() => {
            if (scrollDownArrow) {
              (scrollDownArrow as HTMLElement).style.display = 'none'
            }
          }, 500)
        }
      }
    }

    let scrollTimeout: NodeJS.Timeout
    const handleScroll = () => {
      const scrollY = window.scrollY || window.pageYOffset
      if (scrollY > 100) {
        hideIndicators()
      }
    }

    window.addEventListener('scroll', handleScroll, { passive: true })
    window.addEventListener('wheel', () => {
      clearTimeout(scrollTimeout)
      scrollTimeout = setTimeout(() => {
        if (window.scrollY > 50) {
          hideIndicators()
        }
      }, 300)
    }, { passive: true })

    setTimeout(hideIndicators, 10000)

    return () => {
      window.removeEventListener('scroll', handleScroll)
      clearTimeout(scrollTimeout)
    }
  }, [])

  // Setup Intersection Observer for performance
  useEffect(() => {
    const canvasContainer = document.getElementById('canvas-container')
    if (!canvasContainer || !isReady) return

    let isCanvasVisible = true
    let originalAnimationLoop: (() => void) | null = null

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        const wasVisible = isCanvasVisible
        isCanvasVisible = entry.isIntersecting
        
        const experience = experienceRef.current
        if (wasVisible !== isCanvasVisible && experience && experience.renderer) {
          if (isCanvasVisible) {
            // Resume animation
            if (experience.renderer.instance && originalAnimationLoop) {
              experience.renderer.instance.setAnimationLoop(originalAnimationLoop)
            }
            if (experience.time) {
              experience.time.playing = true
            }
          } else {
            // Pause animation
            if (experience.renderer.instance) {
              experience.renderer.instance.setAnimationLoop(null)
            }
            if (experience.time) {
              experience.time.playing = false
            }
          }
        }
      })
    }, {
      threshold: 0.1
    })
    
    observer.observe(canvasContainer)

    // Store animation loop reference when ready
    const handleReady = () => {
      setTimeout(() => {
        const experience = experienceRef.current
        if (experience && experience.renderer && experience.renderer.instance) {
          originalAnimationLoop = async () => {
            if (experience && isCanvasVisible) {
              await experience.update()
            }
          }
        }
      }, 100)
    }

    window.addEventListener('3d-app:classes-ready', handleReady)

    return () => {
      observer.disconnect()
      window.removeEventListener('3d-app:classes-ready', handleReady)
    }
  }, [isReady])

  return (
    <>
      <canvas ref={canvasRef} className="webgl" />
      <button
        id="test-zoom-button"
        className={`test-zoom-button ${isZooming ? 'zooming' : ''}`}
        onClick={handleZoomClick}
        disabled={isZooming}
      >
        {buttonText}
      </button>
    </>
  )
}

