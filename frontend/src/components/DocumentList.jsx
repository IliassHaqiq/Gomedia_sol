import { useState, useEffect } from 'react'
import axios from 'axios'

export default function DocumentList({ apiKey, onSelectDocument, selectedDocumentId }) {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchDocuments = async () => {
    setLoading(true)
    setError(null)

    try {
      const headers = {}
      if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`
      }

      const response = await axios.get('/api/documents/', { headers })
      setDocuments(response.data || [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement des documents')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
    const interval = setInterval(fetchDocuments, 10000) // Refresh every 10s
    return () => clearInterval(interval)
  }, [apiKey])

  const refreshDocuments = () => {
    fetchDocuments()
  }

  const extractDocument = async (docId) => {
    try {
      const headers = {}
      if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`
      }

      await axios.post(
        `/api/documents/${docId}/extract`,
        {},
        { headers }
      )

      alert('✅ Extraction démarrée !')
      fetchDocuments()
    } catch (err) {
      alert(`❌ Erreur extraction: ${err.response?.data?.detail || err.message}`)
    }
  }

  const deleteDocument = async (docId) => {
    if (!window.confirm('Supprimer ce document et ses spécifications ?')) return

    try {
      const headers = {}
      if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`
      }

      // Note: API doesn't have delete endpoint yet, this is for future
      alert('Fonctionnalité de suppression à implémenter côté serveur')

      // For now, just refresh
      fetchDocuments()
    } catch (err) {
      alert(`❌ Erreur suppression: ${err.response?.data?.detail || err.message}`)
    }
  }

  if (loading) {
    return <div className="loading">📡 Chargement des documents...</div>
  }

  if (error) {
    return <div className="error">❌ {error}</div>
  }

  return (
    <div className="document-section">
      <div className="section-header">
        <h2 className="section-title">
          📋 Documents ({documents.length})
        </h2>
        <button onClick={refreshDocuments} className="btn-refresh">
          🔄 Rafraîchir
        </button>
      </div>

      {documents.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📄</div>
          <p>Aucun document. Utilisez la section Upload pour ajouter des fichiers.</p>
        </div>
      ) : (
        <div className="document-grid">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className={`document-card ${selectedDocumentId === doc.id ? 'selected' : ''}`}
              onClick={() => onSelectDocument(doc.id)}
            >
              <div className="doc-header">
                <div>
                  <div className="doc-title" title={doc.filename}>
                    {doc.filename}
                  </div>
                  <div className="doc-info">
                    ID: {doc.id} • {new Date(doc.uploaded_at).toLocaleDateString()}
                  </div>
                </div>
                <div className={`doc-status status-${doc.status}`}>
                  {doc.status}
                </div>
              </div>

              <div className="doc-actions">
                {doc.status === 'uploaded' && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      extractDocument(doc.id)
                    }}
                    className="btn btn-success"
                  >
                    🔍 Extraire
                  </button>
                )}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    deleteDocument(doc.id)
                  }}
                  className="btn btn-danger"
                >
                  🗑️ Supprimer
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
