export default [
    // {
    //     name: 'exampleSound',
    //     type: 'audio',
    //     path: './sounds/example.mp3'
    // },
    // {
    //     name: 'exampleModel',
    //     type: 'gltfModel',
    //     path: './models/example.glb'
    // },
    // {
    //     name: 'exampleModel',
    //     type: 'gltfModel',
    //     path: './models/points_3.glb',
    //     meta: {
    //         "type": "gltfModel"
    //     }
    // },
    // {
    //     name: 'exampleAttribute',
    //     type: 'json',
    //     path: './models/attr.json',
    //     meta: {
    //         "type": "json"
    //     }
    // },

    {
        name: 'displacementTexture',
        type: 'texture',
        obfuscate: true,
        path: '/static/textures/displacement.jpg',
        meta: {
            "type": "texture"
        }
    },
    {
        name: 'foxModel',
        type: 'gltfModel',
        obfuscate: true,
        path: '/static/models/fox.glb',
        meta: {
            "type": "gltfModel"
        }
    },
    {
        name: 'damagedHelmetModel',
        type: 'gltfModel',
        obfuscate: true,
        path: '/static/models/DamagedHelmet.glb',
        meta: {
            "type": "gltfModel"
        }
    },

    // Grass
    {
        name: 'grass1Texture',
        type: 'texture',
        obfuscate: true,
        path: '/static/textures/grass/grass1.png',
        meta: {
            "type": "texture"
        }
    },
    {
        name: 'grass2Texture',
        type: 'texture',
        obfuscate: true,
        path: '/static/textures/grass/grass2.png',
        meta: {
            "type": "texture"
        }
    },
    {
        name: 'gridTexture',
        type: 'texture',
        obfuscate: true,
        path: '/static/textures/grass/grid.png',
        meta: {
            "type": "texture"
        }
    },
    {
        name: 'tileDataTexture',
        type: 'texture',
        obfuscate: true,
        path: '/static/textures/grass/tileData.jpg',
        meta: {
            "type": "texture"
        }
    },
    {
        name: 'starsTexture',
        type: 'texture',
        obfuscate: true,
        path: '/static/textures/hdr/nebula.png',
        meta: {
            "type": "exrTexture"
        }
    },
    {
        name: 'noiseDeepTexture',
        type: 'texture',
        obfuscate: true,
        path: '/static/textures/noise_deep.png',
        meta: {
            "type": "texture"
        }
    },
]
