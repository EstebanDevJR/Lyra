export default function TechnologiesSection() {
  return (
    <div className="card-section">
      <h3 className="section-title">Tecnologías</h3>
      <p className="info-text">
        El sistema integra <strong>OCR</strong> para extracción de texto, <strong>embeddings</strong> para análisis semántico, y una arquitectura <strong>multiagente en LangChain</strong> que simula el flujo de trabajo de un investigador digital.
      </p>
      <div className="tech-badges">
        <span className="tech-badge">OCR</span>
        <span className="tech-badge">Embeddings</span>
        <span className="tech-badge">LangChain</span>
        <span className="tech-badge">Pinecone</span>
        <span className="tech-badge">OpenAI</span>
        <span className="tech-badge">Multi-Agent</span>
      </div>
    </div>
  )
}

