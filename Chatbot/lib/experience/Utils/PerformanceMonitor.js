// Performance optimization utility for Three.js WebGPU experience
// Provides adaptive quality settings and performance monitoring

export class PerformanceMonitor {
    constructor() {
        this.fps = 60
        this.frameCount = 0
        this.lastTime = performance.now()
        this.fpsHistory = []
        this.maxHistoryLength = 60 // 1 second at 60fps
        
        this.qualityLevel = this.detectInitialQuality()
        this.canDowngrade = true
        this.lastDowngradeTime = 0
        this.downgradeThreshold = 30 // FPS threshold for downgrade
        this.upgradeThreshold = 55 // FPS threshold for upgrade
    }

    detectInitialQuality() {
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
        const cores = navigator.hardwareConcurrency || 2
        const memory = navigator.deviceMemory || 4

        if (isMobile || cores <= 2 || memory <= 2) {
            return 'low'
        } else if (cores <= 4 || memory <= 4) {
            return 'medium'
        } else {
            return 'high'
        }
    }

    update() {
        const now = performance.now()
        const delta = now - this.lastTime
        
        if (delta >= 1000) { // Update FPS every second
            this.fps = Math.round((this.frameCount * 1000) / delta)
            this.fpsHistory.push(this.fps)
            
            if (this.fpsHistory.length > this.maxHistoryLength) {
                this.fpsHistory.shift()
            }
            
            this.frameCount = 0
            this.lastTime = now
            
            // Auto-adjust quality if needed
            this.autoAdjustQuality()
        }
        
        this.frameCount++
    }

    getAverageFPS() {
        if (this.fpsHistory.length === 0) return 60
        return this.fpsHistory.reduce((a, b) => a + b, 0) / this.fpsHistory.length
    }

    autoAdjustQuality() {
        const avgFPS = this.getAverageFPS()
        const now = Date.now()
        
        // Only adjust every 3 seconds to avoid flickering
        if (now - this.lastDowngradeTime < 3000) return
        
        if (avgFPS < this.downgradeThreshold && this.canDowngrade) {
            if (this.qualityLevel === 'high') {
                this.qualityLevel = 'medium'
                this.lastDowngradeTime = now
                console.warn(`⚠️ Performance downgrade to MEDIUM (avg FPS: ${avgFPS.toFixed(1)})`)
                return 'downgrade'
            } else if (this.qualityLevel === 'medium') {
                this.qualityLevel = 'low'
                this.lastDowngradeTime = now
                this.canDowngrade = false // Don't go lower than low
                console.warn(`⚠️ Performance downgrade to LOW (avg FPS: ${avgFPS.toFixed(1)})`)
                return 'downgrade'
            }
        } else if (avgFPS > this.upgradeThreshold && this.qualityLevel !== 'high') {
            if (this.qualityLevel === 'low') {
                this.qualityLevel = 'medium'
                this.lastDowngradeTime = now
                console.log(`✅ Performance upgrade to MEDIUM (avg FPS: ${avgFPS.toFixed(1)})`)
                return 'upgrade'
            } else if (this.qualityLevel === 'medium') {
                this.qualityLevel = 'high'
                this.lastDowngradeTime = now
                console.log(`✅ Performance upgrade to HIGH (avg FPS: ${avgFPS.toFixed(1)})`)
                return 'upgrade'
            }
        }
        
        return null
    }

    getQualityLevel() {
        return this.qualityLevel
    }

    getCurrentFPS() {
        return this.fps
    }
}

// Quality presets for different components
export const QualityPresets = {
    blackHole: {
        low: {
            iterations: 32,
            stepSize: 0.014,
            noiseFactor: 0.005,
            geometrySegments: 12
        },
        medium: {
            iterations: 64,
            stepSize: 0.01,
            noiseFactor: 0.008,
            geometrySegments: 16
        },
        high: {
            iterations: 96,
            stepSize: 0.0071,
            noiseFactor: 0.01,
            geometrySegments: 20
        },
        ultra: {
            iterations: 128,
            stepSize: 0.005,
            noiseFactor: 0.012,
            geometrySegments: 24
        }
    },
    renderer: {
        low: {
            pixelRatio: 0.75,
            antialias: false,
            shadows: false,
            toneMappingExposure: 1.0
        },
        medium: {
            pixelRatio: 1.0,
            antialias: false,
            shadows: false,
            toneMappingExposure: 1.1
        },
        high: {
            pixelRatio: 1.5,
            antialias: true,
            shadows: true,
            toneMappingExposure: 1.2
        },
        ultra: {
            pixelRatio: 2.0,
            antialias: true,
            shadows: true,
            toneMappingExposure: 1.2
        }
    }
}

