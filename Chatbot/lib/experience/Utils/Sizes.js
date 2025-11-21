import * as THREE from "three";
import EventEmitter from './EventEmitter.js'

import Experience from '@experience/Experience.js'
import { uniform } from 'three/tsl'

export default class Sizes extends EventEmitter {
    constructor() {
        super()

        this.exprience = Experience.getInstance()
        this.isMobile = this.exprience.isMobile

        // Setup
        this.pixelRatio = this.isMobile? 1 : Math.min( window.devicePixelRatio, 2 )
        this.width = window.innerWidth
        this.height = window.innerHeight

        this.width_DPR = this.width * window.devicePixelRatio
        this.height_DPR = this.height * window.devicePixelRatio

        this.aspectRatio = this.width / this.height

        this.uniforms = {
            resolution: uniform( new THREE.Vector2( this.width, this.height ) ),
            aspectRatio: uniform( this.aspectRatio ),
            width_DPR: uniform( this.width_DPR ),
            height_DPR: uniform( this.height_DPR ),
        }

        // Resize event con throttling para mejor performance
        let resizeTimeout
        const handleResize = () => {
            // Cancelar timeout anterior si existe
            if (resizeTimeout) {
                clearTimeout(resizeTimeout)
            }
            
            // Throttle: ejecutar después de 16ms (aproximadamente 60fps)
            resizeTimeout = setTimeout(() => {
                this.pixelRatio = this.isMobile? 1 : Math.min( window.devicePixelRatio, 2 )
                this.width = window.innerWidth
                this.height = window.innerHeight

                this.width_DPR = this.width * window.devicePixelRatio
                this.height_DPR = this.height * window.devicePixelRatio

                this.aspectRatio = this.width / this.height

                this.uniforms.resolution.value.set( this.width, this.height )
                this.uniforms.aspectRatio.value = this.aspectRatio
                this.uniforms.width_DPR.value = this.width_DPR
                this.uniforms.height_DPR.value = this.height_DPR

                this.trigger( 'resize' )
            }, 16) // ~60fps
        }
        
        window.addEventListener( 'resize', handleResize, { passive: true } )
    }

}
