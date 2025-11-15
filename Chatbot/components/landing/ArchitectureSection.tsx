export default function ArchitectureSection() {
  return (
    <div className="card-section">
      <h3 className="section-title">Arquitectura Multiagente</h3>
      <p className="info-text">
        Todo el proceso es orquestado por un <strong>Supervisor Agent</strong> que decide inteligentemente qué herramientas y agentes especializados activar según la solicitud del usuario.
      </p>
      <p className="info-text">
        Cada agente tiene un rol específico: extracción, limpieza, análisis, resumen, validación y respuesta, trabajando en conjunto para proporcionar resultados precisos y contextualizados.
      </p>
    </div>
  )
}

