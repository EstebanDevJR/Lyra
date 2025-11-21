import * as THREE from 'three/webgpu'
import Experience from '@experience/Experience.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { TransformControls } from 'three/addons/controls/TransformControls.js';
import { isMobile } from '@experience/Utils/Helpers/Global/isMobile.js'
import gsap from "gsap";

export default class Camera
{
    constructor( parameters = {} )
    {
        this.experience = new Experience()
        this.renderer = this.experience.renderer.instance
        this.sizes = this.experience.sizes
        this.time = this.experience.time
        this.canvas = this.experience.canvas
        this.timeline = this.experience.timeline
        this.scene = parameters.world.scene
        this.cursorEnabled = false
        this.isMobileDevice = isMobile.any()

        this.lerpVector = new THREE.Vector3();

        this.setInstance()
        this.setControls()
    }

    setInstance()
    {
        //const FOV = this.experience.isMobile ? 35 : 25
        this.instance = new THREE.PerspectiveCamera(50, this.sizes.width / this.sizes.height, 0.1, 2000)
        
        // Fixed camera position for mobile (optimized view)
        if (this.isMobileDevice) {
            this.defaultCameraPosition = new THREE.Vector3(1.2, 0.4, 3.2)
            console.log('📱 Camera set to fixed position for mobile')
        } else {
            this.defaultCameraPosition = new THREE.Vector3(1, 0.5, 3)
        }

        this.instance.position.copy(this.defaultCameraPosition)
        this.instance.lookAt(new THREE.Vector3(0, 0, 0));

        this.lerpVector.copy(this.instance.position);
    }

    setControls()
    {
        this.controls = new OrbitControls(this.instance, this.canvas)
        this.controls.enableDamping = true
        
        // Bloquear zoom - fijar distancia mínima y máxima iguales
        const fixedDistance = this.instance.position.length()
        this.controls.minDistance = fixedDistance
        this.controls.maxDistance = fixedDistance
        
        // Deshabilitar zoom completamente
        this.controls.enableZoom = false
        
        // Permitir solo rotación
        this.controls.enablePan = false
        
        // CRITICAL: Disable OrbitControls on mobile to allow scroll
        if (this.isMobileDevice) {
            this.controls.enabled = false
            console.log('📱 OrbitControls disabled on mobile for scroll compatibility')
        } else {
            this.controls.enabled = true
            console.log('🖱️ OrbitControls enabled on desktop')
        }
        
        this.controls.target = new THREE.Vector3(0, 0, 0)


        this.transformControls = new TransformControls( this.instance, this.renderer.domElement );
        //this.transformControls.addEventListener( 'change', render );
        this.transformControls.addEventListener( 'dragging-changed', ( event ) => {
            this.controls.enabled = ! event.value;
        } );

        this.scene.add( this.transformControls.getHelper() );

        this._setListeners()
    }

    _setListeners() {
        const control = this.transformControls;
        window.addEventListener( 'keydown', ( event ) => {

            switch ( event.key ) {

                case 'q':
                    control.setSpace( control.space === 'local' ? 'world' : 'local' );
                    break;

                case 'Shift':
                    control.setTranslationSnap( 1 );
                    control.setRotationSnap( THREE.MathUtils.degToRad( 15 ) );
                    control.setScaleSnap( 0.25 );
                    break;

                case 'w':
                    control.setMode( 'translate' );
                    break;

                case 'e':
                    control.setMode( 'rotate' );
                    break;

                case 'r':
                    control.setMode( 'scale' );
                    break;

                case '+':
                case '=':
                    control.setSize( control.size + 0.1 );
                    break;

                case '-':
                case '_':
                    control.setSize( Math.max( control.size - 0.1, 0.1 ) );
                    break;

                case 'x':
                    control.showX = ! control.showX;
                    break;

                case 'y':
                    control.showY = ! control.showY;
                    break;

                case 'z':
                    control.showZ = ! control.showZ;
                    break;

                case ' ':
                    control.enabled = ! control.enabled;
                    break;

                case 'Escape':
                    control.reset();
                    break;

            }

        } );

        window.addEventListener( 'keyup', function ( event ) {

            switch ( event.key ) {

                case 'Shift':
                    control.setTranslationSnap( null );
                    control.setRotationSnap( null );
                    control.setScaleSnap( null );
                    break;

            }

        } );
    }

    resize()
    {
        this.instance.aspect = this.sizes.width / this.sizes.height
        this.instance.updateProjectionMatrix()
    }

    update()
    {
        // Skip controls update on mobile for performance
        if (!this.isMobileDevice) {
            this.controls?.update()
        }

        this.instance.updateMatrixWorld() // To be used in projection
    }

    animateCameraPosition() {

    }
}
