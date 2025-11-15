import Image from 'next/image'

export default function InfoHero() {
  return (
    <div className="info-hero">
      <div className="info-title-container fade-in-up">
        <Image
          src="/images/logo.png"
          alt="Lyra Logo"
          width={80}
          height={80}
          className="info-logo"
          priority
        />
        <h2 className="info-title">Lyra</h2>
      </div>
      <p className="info-tagline fade-in-up" style={{ animationDelay: '0.1s' }}>
        Asistente de Inteligencia Artificial para Análisis Científico Astronómico
      </p>
    </div>
  )
}

