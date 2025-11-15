import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  // Configuración para Turbopack (Next.js 16+)
  turbopack: {
    resolveAlias: {
      '@experience': path.resolve(__dirname, 'lib/experience'),
    },
    resolveExtensions: ['.js', '.jsx', '.ts', '.tsx', '.json'],
  },
  // Configuración de webpack como fallback (se usará si se ejecuta con --webpack)
  webpack: (config, { isServer }) => {
    // Configurar alias para @experience
    config.resolve.alias = {
      ...config.resolve.alias,
      '@experience': path.resolve(__dirname, 'lib/experience'),
    }
    
    // Permitir archivos .js en imports
    config.resolve.extensions.push('.js')
    
    return config
  },
}

export default nextConfig
