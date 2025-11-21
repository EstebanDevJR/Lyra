import * as THREE from 'three/webgpu'
import EventEmitter from './Utils/EventEmitter.js'

import Debug from './Utils/Debug.js'
import Sizes from './Utils/Sizes.js'
import Time from './Utils/Time.js'
import Renderer from './Renderer.js'
import Worlds from './Worlds.js'
import Resources from './Utils/Resources.js'
import Sound from "./Utils/Sound.js";

import sources from './Sources.js'
import gsap from "gsap";
import MotionPathPlugin from "gsap/MotionPathPlugin";
import State from './State.js'
import PostProcess from './Utils/PostProcess.js'

import { isMobile } from '@experience/Utils/Helpers/Global/isMobile';
import Ui from "@experience/Ui/Ui.js";

export default class Experience extends EventEmitter {

    static _instance = null

    appLoaded = false;
    firstRender = false;

    static getInstance() {
        return Experience._instance || new Experience()
    }

    constructor( _canvas ) {
        super()
        // Singleton
        if ( Experience._instance ) {
            return Experience._instance
        }
        Experience._instance = this

        // Global access
        window.experience = this

        // Html Elements
        this.html = {}
        this.html.preloader = typeof document !== 'undefined' ? document.getElementById( "preloader" ) : null
        this.html.playButton = typeof document !== 'undefined' ? document.getElementById( "play-button" ) : null

        this.isMobile = isMobile.any()

        // Options
        this.canvas = _canvas

        if ( !this.canvas ) {
            console.warn( 'Missing \'Canvas\' property' )
            return
        }

        this.setDefaultCode();

        this.init()
    }

    init() {
        // Start Loading Resources

        // Setup
        this.timeline = gsap.timeline({
            paused: true,
        });
        this.debug = new Debug()
        this.sizes = new Sizes()
        this.time = new Time()
        this.ui = new Ui()
        this.renderer = new Renderer()
        this.state = new State()
        this.sound = new Sound()

        this.resources = new Resources( sources )


        this.mainCamera = undefined
        this.mainScene = undefined

        if ( this.state.postprocessing ) {
            this.postProcess = new PostProcess( this.renderer.instance )
        }

        // Wait for resources
        this.resources.on( 'ready', () => {
            setTimeout( () => {
                if (typeof window !== 'undefined' && window.preloader && window.preloader.hidePreloader) {
                    window.preloader.hidePreloader()
                }
            }, 1000)

            this.time.reset()

            this.worlds = new Worlds()

            this.postInit()
            this.setListeners()
            this.animationPipeline();

            this.trigger("classesReady");
            window.dispatchEvent( new CustomEvent( "3d-app:classes-ready" ) );

            this.appLoaded = true
        } )
    }

    animationPipeline() {
        this.worlds?.animationPipeline()
    }

    postInit() {
        this.renderer.postInit()
        this.postProcess?.postInit()
        this.worlds?.postInit()
        this.debug?.postInit()
    }

    resize() {
        this.worlds.resize()
        this.renderer.resize()
        this.postProcess?.resize()
        this.debug?.resize()
        this.state?.resize()
        this.sound?.resize()
    }

    async render() {
        if ( this.state.postprocessing ) {
            return this.postProcess.update( this.time.delta )
        } else {
            return this.renderer.update( this.time.delta )
        }
    }

    async update() {
        this.worlds.update( this.time.delta )

        this.render()

        if ( this.debug.active ) {
            this.debug.update( this.time.delta )
        }

        await this.postUpdate( this.time.delta )

        this.debug?.stats?.update();
    }

    _fireReady() {
        this.trigger( 'ready' )
        window.dispatchEvent( new CustomEvent( "3d-app:ready" ) );

        this.firstRender = 'done';
    }

    async postUpdate( deltaTime ) {
        if ( this.firstRender === true ) {
            window.dispatchEvent( new CustomEvent( "app:first-render" ) );

            // Dispatch event
            this._fireReady();
        }

        // Once Await First Stable Render
        if ( this.resources.loadedAll && this.appLoaded && this.firstRender === false ) {
            await this.render()
            this.firstRender = true;
        }

        this.worlds.postUpdate( deltaTime )
    }

    setListeners() {
        // Resize event
        this.sizes.on( 'resize', () => {
            this.resize()
        } )

        this.renderer.instance.setAnimationLoop( async () => this.update() )
    }

    setDefaultCode() {
        document.ondblclick = function ( e ) {
            e.preventDefault()
        }

        gsap.registerPlugin( MotionPathPlugin );
    }

    startWithPreloader() {
        this.ui.playButton.classList.add( "fade-in" );
        this.ui.playButton.addEventListener( 'click', () => {

            this.ui.playButton.classList.replace( "fade-in", "fade-out" )

            setTimeout( () => {
                this.time.reset()

                // Setup
                this.setupWorlds()

                // Remove preloader
                this.ui.preloader.classList.add( "preloaded" );
                setTimeout( () => {
                    this.ui.preloader.remove();
                    this.ui.playButton.remove();
                }, 2500 );
            }, 100 );
        }, { once: true } );
    }

    destroy() {
        // Safely remove event listeners
        if ( this.sizes ) {
            this.sizes.off( 'resize' )
        }
        if ( this.time ) {
            this.time.off( 'tick' )
        }

        // Traverse the whole scene if it exists
        const sceneToDispose = this.mainScene || ( this.worlds?.mainWorld?.scene )
        if ( sceneToDispose && typeof sceneToDispose.traverse === 'function' ) {
            sceneToDispose.traverse( ( child ) => {
                // Test if it's a mesh
                if ( child instanceof THREE.Mesh ) {
                    if ( child.geometry ) {
                        child.geometry.dispose()
                    }

                    // Loop through the material properties
                    if ( child.material ) {
                        for ( const key in child.material ) {
                            const value = child.material[ key ]

                            // Test if there is a dispose function
                            if ( value && typeof value.dispose === 'function' ) {
                                value.dispose()
                            }
                        }
                    }
                }
            } )
        }

        // Dispose camera controls if they exist
        const cameraToDispose = this.mainCamera || ( this.worlds?.mainWorld?.camera )
        if ( cameraToDispose && cameraToDispose.controls && typeof cameraToDispose.controls.dispose === 'function' ) {
            cameraToDispose.controls.dispose()
        }

        // Dispose renderer if it exists
        if ( this.renderer && this.renderer.instance && typeof this.renderer.instance.dispose === 'function' ) {
            this.renderer.instance.dispose()
        }

        // Dispose debug UI if active
        if ( this.debug && this.debug.active && this.debug.ui && typeof this.debug.ui.destroy === 'function' ) {
            this.debug.ui.destroy()
        }

        // Dispose worlds if they exist
        if ( this.worlds && typeof this.worlds.destroy === 'function' ) {
            this.worlds.destroy()
        }

        // Dispose post process if it exists
        if ( this.postProcess && typeof this.postProcess.destroy === 'function' ) {
            this.postProcess.destroy()
        }
    }
}
