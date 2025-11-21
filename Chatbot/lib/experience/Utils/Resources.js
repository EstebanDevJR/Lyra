import * as THREE from 'three/webgpu'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import { FontLoader } from 'three/examples/jsm/loaders/FontLoader.js'
import { HDRLoader } from 'three/examples/jsm/loaders/HDRLoader.js'
import { EXRLoader } from 'three/examples/jsm/loaders/EXRLoader.js'
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js'
import { KTX2Loader } from 'three/examples/jsm/loaders/KTX2Loader.js'
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js'
import EventEmitter from './EventEmitter.js'

//import Obfuscate from '@experience/Utils/Helpers/Obfuscate.js';
import Experience from "@experience/Experience.js";

export default class Resources extends EventEmitter {
    experience = Experience.getInstance()
    renderer = experience.renderer.instance

    constructor( sources ) {
        super()

        this.sources = sources
        // this.sourcesFilter()
        // this.obfuscate = Obfuscate.getInstance()

        this.items = {}
        this.toLoad = this.sources.length
        this.loaded = 0
        this.loadedAll = false

        this.setLoaders()
        this.startLoading()
    }

    sourcesFilter() {
        if ( import.meta.env.MODE === "development" ) {
            return true
        }

        this.sources.forEach( source => {
            if ( source.obfuscate === true ) {
                if ( source.type.match( /model/i ) ) {
                    // replace .glb, .gltf, .obj with .bin
                    source.path = source.path.replace( /\.(glb|gltf|obj)/i, '.bin' )
                    source.type = 'binModel'
                }

                if ( source.type === 'json' ) {
                    // replace image name to .bin
                    source.path = source.path.replace( /\.(json)/i, '.bin' )
                    source.type = 'binJson'
                }

                if ( source.type.match( /texture/i ) ) {
                    // replace image name to .bin
                    source.path = source.path.replace( /\.(jpg|jpeg|png)/i, '.bin' )
                    source.type = 'binTexture'
                }
            }
        } )
    }

    setLoaders() {
        this.loaders = {}
        this.loaders.gltfLoader = new GLTFLoader()
        this.loaders.objLoader = new OBJLoader()
        this.loaders.textureLoader = new THREE.TextureLoader()
        this.loaders.cubeTextureLoader = new THREE.CubeTextureLoader()
        this.loaders.HDRLoader = new HDRLoader()
        this.loaders.EXRLoader = new EXRLoader()
        this.loaders.fontLoader = new FontLoader()
        this.loaders.AudioLoader = new THREE.AudioLoader()

        // add DRACOLoader
        const dracoLoader = new DRACOLoader()
        dracoLoader.setDecoderPath( '/draco/' )

        const ktx2Loader = new KTX2Loader();
        ktx2Loader.setTranscoderPath( '/basis/' );
        ktx2Loader.detectSupportAsync(this.renderer);

        this.loaders.gltfLoader.setDRACOLoader( dracoLoader )
        this.loaders.gltfLoader.setKTX2Loader( ktx2Loader );
        this.loaders.gltfLoader.setMeshoptDecoder( MeshoptDecoder );
    }

    startLoading() {
        // Load each source
        for ( const source of this.sources ) {
            switch ( source.type ) {
                case 'binModel':
                    this.obfuscate.loadFile( source.path, ( arrayBuffer ) => {
                        this.obfuscate.decode( arrayBuffer, source.path, ( model ) => {
                            this.sourceLoaded( source, model )
                        } )
                    } )
                    break

                case 'binJson':
                    this.obfuscate.loadFile( source.path, ( arrayBuffer ) => {
                        this.obfuscate.decode( arrayBuffer, source.path, ( json ) => {
                            this.sourceLoaded( source, json )
                        } )
                    } )
                    break

                case 'binTexture':
                    this.obfuscate.loadFile( source.path, ( arrayBuffer ) => {
                        this.obfuscate.decode( arrayBuffer, source.path, ( textureBuffer ) => {

                            const blob = new Blob( [ textureBuffer ] );
                            createImageBitmap( blob ).then( ( imageBitmap ) => {
                                const texture = new THREE.Texture( imageBitmap )
                                texture.needsUpdate = true
                                this.sourceLoaded( source, texture )
                            } ).catch( err => console.error( "Error texture loading:", err ) )

                        } )
                    } )
                    break

                case 'gltfModel':
                    this.loaders.gltfLoader.load(
                        source.path,
                        ( file ) => {
                            this.sourceLoaded( source, file )
                        },
                        undefined,
                        ( error ) => {
                            console.error( `Error loading model ${source.name}:`, error )
                            // Continuar aunque falle un modelo
                            this.sourceLoaded( source, null )
                        }
                    )
                    break

                case 'objModel':
                    this.loaders.objLoader.load(
                        source.path,
                        ( file ) => {
                            this.sourceLoaded( source, file )
                        }
                    )
                    break

                case 'texture':
                    this.loaders.textureLoader.load(
                        source.path,
                        ( file ) => {
                            // Optimizaciones de textura
                            file.generateMipmaps = true
                            file.minFilter = THREE.LinearMipmapLinearFilter
                            file.magFilter = THREE.LinearFilter
                            // Configurar wrap mode según necesidad
                            file.wrapS = THREE.RepeatWrapping
                            file.wrapT = THREE.RepeatWrapping

                            this.sourceLoaded( source, file )
                        },
                        undefined,
                        ( error ) => {
                            console.error( `Error loading texture ${source.name}:`, error )
                            // Continuar aunque falle una textura
                            this.sourceLoaded( source, null )
                        }
                    )
                    break

                case 'videoTexture':
                    let videoElement = document.createElement( 'video' )
                    videoElement.src = source.path
                    videoElement.setAttribute( 'crossorigin', 'anonymous' )
                    videoElement.muted = true
                    videoElement.loop = true
                    videoElement.load()
                    videoElement.setAttribute( 'playsinline', '' )
                    videoElement.setAttribute( 'webkit-playsinline', '' )
                    videoElement.play()

                    const obj = {
                        videoTexture: new THREE.VideoTexture( videoElement ),
                        videoElement: videoElement
                    }

                    videoElement.addEventListener( 'canplaythrough', () => {
                        this.sourceLoaded( source, obj )
                    } )
                    break

                case 'cubeTexture':
                    this.loaders.cubeTextureLoader.load(
                        source.path,
                        ( file ) => {
                            this.sourceLoaded( source, file )
                        }
                    )
                    break

                case 'rgbeTexture':
                    this.loaders.HDRLoader.load(
                        source.path,
                        ( file ) => {
                            this.sourceLoaded( source, file )
                        }
                    )
                    break

                case 'hdrTexture':
                    this.loaders.HDRLoader.load(
                        source.path,
                        ( file ) => {
                            this.sourceLoaded( source, file )
                        }
                    )
                    break

                case 'exrTexture':
                    this.loaders.EXRLoader.load(
                        source.path,
                        ( file ) => {
                            this.sourceLoaded( source, file )
                        }
                    )
                    break

                case 'font':
                    this.loaders.fontLoader.load(
                        source.path,
                        ( file ) => {
                            this.sourceLoaded( source, file )
                        }
                    )
                    break

                case 'audio':
                    this.loaders.AudioLoader.load(
                        source.path,
                        ( file ) => {
                            this.sourceLoaded( source, file )
                        }
                    )
                    break
                case 'json':
                    fetch( source.path )
                        .then( response => {
                            if (!response.ok) {
                                throw new Error(`HTTP error! status: ${response.status}`)
                            }
                            return response.json()
                        } )
                        .then( data => {
                            this.sourceLoaded( source, data )
                        } )
                        .catch( error => {
                            console.error( `Error loading JSON ${source.name}:`, error )
                            this.sourceLoaded( source, null )
                        } )
                    break
            }

        }

        if ( this.sources.length === 0 ) {
            setTimeout( () => {
                this.loadedAll = true
                this.trigger( 'ready' )
            } );
        }
    }

    sourceLoaded( source, file ) {
        this.items[ source.name ] = file

        this.loaded++

        if ( this.loaded === this.toLoad ) {
            this.loadedAll = true
            this.trigger( 'ready' )
        }
    }
}
