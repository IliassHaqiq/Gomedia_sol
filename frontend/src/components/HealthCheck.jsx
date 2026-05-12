import { useState, useEffect } from 'react'
import axios from 'axios'

export default function HealthCheck() {
  const [healthStatus, setHealthStatus] = useState({
    api: { status: 'checking', message: 'En attente...' },
    db: { status: 'checking', message: 'En attente...' },
    ollama: { status: 'checking', message: 'En attente...' },
  })
  const [checking, setChecking] = useState(false)

  const checkHealth = async () => {
    setChecking(true)

    // Reset all to checking
    setHealthStatus({
      api: { status: 'checking', message: 'Vérification en cours...' },
      db: { status: 'checking', message: 'Vérification en cours...' },
      ollama: { status: 'checking', message: 'Vérification en cours...' },
    })

    const services = [
      { name: 'api', url: 'http://localhost:8000/health', icon: '🌐', title: 'API' },
      { name: 'db', url: 'http://localhost:8000/health/db', icon: '🗄️', title: 'Base de Données' },
      { name: 'ollama', url: 'http://localhost:8000/health/ollama', icon: '🤖', title: 'Service LLM (Gemini)' },
    ]

    for (const service of services) {
      try {
        const response = await axios.get(service.url, { timeout: 5000 })

        setHealthStatus(prev => ({
          ...prev,
          [service.name]: {
            status: 'healthy',
            message: '✅ Service opérationnel',
            data: response.data,
            responseTime: response.headers['x-response-time'] || Date.now(),
          },
        }))
      } catch (error) {
        let errorMessage = '❌ Service inaccessible'

        if (error.code === 'ECONNREFUSED') {
          errorMessage = '❌ Connexion refusée - Service arrêté'
        } else if (error.response) {
          errorMessage = `❌ Erreur ${error.response.status}: ${error.response.data?.error || error.response.data?.detail}`
        } else if (error.request) {
          errorMessage = '❌ Pas de réponse - Service hors ligne'
        } else {
          errorMessage = `❌ Erreur: ${error.message}`
        }

        setHealthStatus(prev => ({
          ...prev,
          [service.name]: {
            status: 'unhealthy',
            message: errorMessage,
            error: error,
          },
        }))
      }
    }

    setChecking(false)
  }

  useEffect(() => {
    // Check health on mount
    checkHealth()
    const interval = setInterval(checkHealth, 30000) // Auto-refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const getCardClass = (status) => {
    return status === 'healthy' ? 'healthy' : status === 'unhealthy' ? 'unhealthy' : ''
  }

  const getIconClass = (status) => {
    return status === 'healthy' ? 'health-healthy' : status === 'unhealthy' ? 'health-unhealthy' : ''
  }

  const allHealthy = Object.values(healthStatus).every(s => s.status === 'healthy')

  return (
    <div className="health-section">
      <div className="health-summary" style={{ marginBottom: '2rem', textAlign: 'center' }}>
        {allHealthy ? (
          <div className="success" style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
            🎉 Tous les services sont opérationnels
          </div>
        ) : (
          <div className="warning" style={{ fontSize: '1.2rem', fontWeight: 'bold' }}>
            ⚠️ Certains services rencontrent des problèmes
          </div>
        )}
      </div>

      <div className="health-grid">
        <div className={`health-card ${getCardClass(healthStatus.api.status)}`}>
          <div className={`health-icon ${getIconClass(healthStatus.api.status)}`}>
            {healthStatus.api.status === 'healthy' ? '✅' : healthStatus.api.status === 'unhealthy' ? '❌' : '⏳'}
          </div>
          <div className={`health-status ${getIconClass(healthStatus.api.status)}`}>
            {healthStatus.api.status === 'checking' ? '⏳ En attente' :
             healthStatus.api.status === 'healthy' ? '✅ API Opérationnelle' :
             '❌ API Hors ligne'}
          </div>
          <div className="health-details" style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
            {healthStatus.api.data && (
              <>
                <div><strong>Version:</strong> {healthStatus.api.data.version}</div>
                <div><strong>Statut:</strong> {healthStatus.api.data.status}</div>
              </>
            )}
            <div><strong>Message:</strong> {healthStatus.api.message}</div>
          </div>
          <button
            className="check-btn"
            onClick={checkHealth}
            disabled={checking}
          >
            {checking ? '⏳ Vérification...' : '🔍 Vérifier'}
          </button>
        </div>

        <div className={`health-card ${getCardClass(healthStatus.db.status)}`}>
          <div className={`health-icon ${getIconClass(healthStatus.db.status)}`}>
            {healthStatus.db.status === 'healthy' ? '🗄️' : healthStatus.db.status === 'unhealthy' ? '🗄️' : '⏳'}
          </div>
          <div className={`health-status ${getIconClass(healthStatus.db.status)}`}>
            {healthStatus.db.status === 'checking' ? '⏳ Vérification...' :
             healthStatus.db.status === 'healthy' ? '🗄️ Base de données OK' :
             '🗄️ Base données inaccessible'}
          </div>
          <div className="health-details" style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
            {healthStatus.db.data && (
              <>
                <div><strong>Service:</strong> {healthStatus.db.data.service}</div>
                <div><strong>Version:</strong> {healthStatus.db.data.version}</div>
              </>
            )}
            <div><strong>Message:</strong> {healthStatus.db.message}</div>
          </div>
        </div>

        <div className={`health-card ${getCardClass(healthStatus.ollama.status)}`}>
          <div className={`health-icon ${getIconClass(healthStatus.ollama.status)}`}>
            {healthStatus.ollama.status === 'healthy' ? '🤖' : healthStatus.ollama.status === 'unhealthy' ? '🤖' : '⏳'}
          </div>
          <div className={`health-status ${getIconClass(healthStatus.ollama.status)}`}>
            {healthStatus.ollama.status === 'checking' ? '⏳ Vérification...' :
             healthStatus.ollama.status === 'healthy' ? '🤖 Gemini Opérationnel' :
             '🤖 Gemini Hors ligne'}
          </div>
          <div className="health-details" style={{ marginTop: '1rem', fontSize: '0.9rem' }}>
            {healthStatus.ollama.data && (
              <>
                <div><strong>Service:</strong> {healthStatus.ollama.data.service}</div>
                <div><strong>Version:</strong> {healthStatus.ollama.data.version}</div>
              </>
            )}
            <div><strong>Message:</strong> {healthStatus.ollama.message}</div>
          </div>
        </div>
      </div>

      <div style={{ marginTop: '2rem', textAlign: 'center', color: 'var(--gray)', fontSize: '0.9rem' }}>
        <p>🔄 Rafraîchi automatiquement toutes les 30 secondes</p>
        <p>⏰ Dernière vérification: {new Date().toLocaleTimeString()}</p>
      </div>
    </div>
  )
}
