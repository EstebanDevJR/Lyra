import * as THREE from 'three/webgpu'
import Experience from './Experience.js'
import State from "./State.js";
import { isMobile } from './Utils/Helpers/Global/isMobile.js'

export default class Renderer {
    constructor() {
        this.experience = new Experience()

        this.canvas = this.experience.canvas
        this.sizes = this.experience.sizes

        this.debug = this.experience.debug
        this.resources = this.experience.resources
        this.html = this.experience.html

        // Device capabilities detection
        this.isMobileDevice = isMobile.any()
        this.isLowEndDevice = this.detectLowEndDevice()

        this.setInstance()
        this.setDebug()
    }

    postInit() {
        this.camera = this.experience.mainCamera.instance
        this.scene = this.experience.mainScene
        this.state = this.experience.state
    }

    detectLowEndDevice() {
        // Detect based on cores, memory, and GPU tier if available
        const cores = navigator.hardwareConcurrency || 4
        const memory = navigator.deviceMemory || 4 // GB
        
        // Only consider truly low-end devices
        // Low-end if: <=2 cores AND <=2GB RAM on mobile
        const isVeryLowEnd = cores <= 2 && memory <= 2
        const isLowEndMobile = this.isMobileDevice && (cores <= 4 || memory <= 3)
        
        return isVeryLowEnd || isLowEndMobile
    }

    setInstance() {
        this.clearColor = '#010101'

        // Determine if we should force WebGL for compatibility
        const forceWebGL = this.isLowEndDevice

        this.instance = new THREE.WebGPURenderer( {
            canvas: this.canvas,
            antialias: !this.isLowEndDevice, // Disable AA on low-end
            alpha: false,
            stencil: false,
            depth: true,
            useLegacyLights: false,
            physicallyCorrectLights: true,
            forceWebGL: forceWebGL
        } )

        this.instance.shadowMap.enabled = !this.isLowEndDevice // Disable shadows on low-end
        this.instance.shadowMap.type = THREE.PCFSoftShadowMap

        this.instance.outputColorSpace = THREE.SRGBColorSpace
        this.instance.setSize( this.sizes.width, this.sizes.height )
        
        // Adaptive pixel ratio based on device
        let targetPixelRatio
        if (this.isLowEndDevice) {
            targetPixelRatio = Math.min(this.sizes.pixelRatio, 1) // Max 1x on low-end
        } else if (this.isMobileDevice) {
            targetPixelRatio = Math.min(this.sizes.pixelRatio, 1.5) // Max 1.5x on mobile
        } else {
            targetPixelRatio = Math.min(this.sizes.pixelRatio, 2) // Max 2x on desktop
        }
        
        this.instance.setPixelRatio( targetPixelRatio )
        this.instance.setClearColor( this.clearColor, 1 )

        this.instance.toneMapping = THREE.ACESFilmicToneMapping
        this.instance.toneMappingExposure = this.isLowEndDevice ? 1.0 : 1.2
        
        console.log(`🖥️ Renderer initialized: ${forceWebGL ? 'WebGL' : 'WebGPU'} | Mobile: ${this.isMobileDevice} | Low-end: ${this.isLowEndDevice} | Pixel Ratio: ${targetPixelRatio}`)
    }

    setDebug() {
        if ( this.debug.active ) {
            if ( this.debug.panel ) {
                const debugFolder = this.debug.panel.addFolder({
                    title: 'Renderer',
                    expanded: false,
                });

                debugFolder.addBinding( this.instance, "toneMapping", {
                    label: "Tone Mapping",
                    options: {
                        "No": THREE.NoToneMapping,
                        "Linear": THREE.LinearToneMapping,
                        "Reinhard": THREE.ReinhardToneMapping,
                        "Cineon": THREE.CineonToneMapping,
                        "ACESFilmic": THREE.ACESFilmicToneMapping,
                        "AgXToneMapping": THREE.AgXToneMapping,
                        "NeutralToneMapping": THREE.NeutralToneMapping
                    }
                } ).on( 'change', () => {
                    if ( this.state.postprocessing ) {
                        this.experience.postProcess.composer.needsUpdate = true
                    }
                })

                debugFolder.addBinding( this.instance, "toneMappingExposure", {
                    min: 0,
                    max: 2,
                    step: 0.01,
                    label: "Tone Mapping Exposure"
                } )
            }

        }
    }

    update() {
        if ( this.debug.active ) {
            this.debugRender()
        } else {
            this.productionRender()
        }
    }

    productionRender() {
        // On mobile with static camera, we can render at lower FPS for performance
        // The scene still updates but less frequently
        if (this.isMobileDevice && !this.needsContinuousRender) {
            // Render at ~30fps instead of 60fps on mobile when static
            if (!this.lastRenderTime || Date.now() - this.lastRenderTime > 33) {
                this.instance.renderAsync( this.scene, this.camera )
                this.lastRenderTime = Date.now()
            }
        } else {
            this.instance.renderAsync( this.scene, this.camera )
        }
    }

    debugRender() {
        this.instance.renderAsync( this.scene, this.camera )
    }
    
    // Call this to force continuous rendering (e.g., during animations)
    setContinuousRender(enabled) {
        this.needsContinuousRender = enabled
    }

    resize() {
        this.instance.setSize( this.sizes.width, this.sizes.height )
        this.instance.setPixelRatio( this.sizes.pixelRatio )
    }

    destroy() {

    }
}
