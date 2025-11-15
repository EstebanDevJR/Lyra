export default function ProcessSteps() {
  const steps = [
    { number: '01', title: 'Extracción', description: 'Extrae el texto usando OCR cuando es necesario, soportando PDFs e imágenes.' },
    { number: '02', title: 'Limpieza', description: 'Limpia y estructura el contenido eliminando ruido y normalizando el texto.' },
    { number: '03', title: 'Análisis Semántico', description: 'Genera embeddings y busca fragmentos relevantes en la base vectorial.' },
    { number: '04', title: 'Procesamiento', description: 'Resume, traduce o amplía el contenido según las necesidades del usuario.' },
    { number: '05', title: 'Cálculos', description: 'Calcula variables físicas como masas, radios y distancias cuando es necesario.' },
    { number: '06', title: 'Respuesta Final', description: 'Genera una respuesta coherente y validada científicamente.' },
  ]

  return (
    <div className="process-steps">
      {steps.map((step, index) => (
        <div 
          key={step.number} 
          className="process-step fade-in-up" 
          style={{ animationDelay: `${0.3 + index * 0.1}s` }}
        >
          <div className="step-number">{step.number}</div>
          <div className="step-content">
            <h4 className="step-title">{step.title}</h4>
            <p className="step-description">{step.description}</p>
          </div>
        </div>
      ))}
    </div>
  )
}

