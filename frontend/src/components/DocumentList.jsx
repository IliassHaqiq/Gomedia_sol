import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

const EXTRACT_TIMEOUT_MS = 720000 // 12 min — doit dépasser OLLAMA_TIMEOUT côté serveur (2 appels LLM)
const POLL_INTERVAL_MS = 8000 // pendant une extraction uniquement

export default function DocumentList({ apiKey, onSelectDocument, selectedDocumentId }) {
  const descriptionLength = localStorage.getItem('descriptionLength') || 'medium'
  const [documents, setDocuments] = useState([])
  const [initialLoading, setInitialLoading] = useState(true)
  const [error, setError] = useState(null)
  const [extractingId, setExtractingId] = useState(null)

  const fetchDocuments = useCallback(
    async ({ silent = false } = {}) => {
      if (!silent) {
        setInitialLoading(true)
      }
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
        if (!silent) {
          setInitialLoading(false)
        }
      }
    },
    [apiKey]
  )

  useEffect(() => {
    fetchDocuments({ silent: false })
  }, [fetchDocuments])

  // Poll uniquement pendant un clic « Extraire » actif (évite la boucle infinie)
  useEffect(() => {
    if (extractingId === null) {
      return undefined
    }

    const interval = setInterval(() => {
      fetchDocuments({ silent: true })
    }, POLL_INTERVAL_MS)

    return () => clearInterval(interval)
  }, [extractingId, fetchDocuments])

  const hasProcessingDoc = documents.some((d) => d.status === 'processing')

  const extractDocument = async (docId) => {
    const target = documents.find((d) => d.id === docId)
    if (target?.status === 'processing') {
      alert('⏳ Extraction déjà en cours pour ce document. Utilisez « Annuler » si elle est bloquée.')
      return
    }
    if (hasProcessingDoc) {
      alert('⏳ Une autre extraction est en cours. Attendez qu\'elle se termine.')
      return
    }

    setExtractingId(docId)
    try {
      const headers = {}
      if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`
      }

      const response = await axios.post(
        `/api/documents/${docId}/extract?description_length=${descriptionLength}`,
        {},
        { headers, timeout: EXTRACT_TIMEOUT_MS }
      )

      const count = response.data?.products?.length ?? 0
      alert(`✅ Extraction terminée — ${count} produit(s) créé(s).`)
      await fetchDocuments({ silent: true })
    } catch (err) {
      const detail = err.response?.data?.detail
      const msg = typeof detail === 'string' ? detail : err.message
      if (err.response?.status === 409) {
        alert(`⏳ ${msg}`)
      } else if (err.code === 'ECONNABORTED') {
        alert('⏱️ Délai dépassé (>12 min). Vérifiez les logs serveur ou réessayez en mode « Court ».')
      } else {
        alert(`❌ Erreur extraction: ${msg}`)
      }
      await fetchDocuments({ silent: true })
    } finally {
      setExtractingId(null)
    }
  }

  const resetDocument = async (docId, e) => {
    e.stopPropagation()
    try {
      const headers = {}
      if (apiKey) headers['Authorization'] = `Bearer ${apiKey}`
      await axios.post(`/api/documents/${docId}/reset`, {}, { headers })
      await fetchDocuments({ silent: true })
    } catch (err) {
      alert(`❌ ${err.response?.data?.detail || err.message}`)
    }
  }

  const deleteDocument = async (e) => {
    e.stopPropagation()
    if (!window.confirm('Supprimer ce document et ses spécifications ?')) return
    alert('Fonctionnalité de suppression à implémenter côté serveur')
    await fetchDocuments({ silent: true })
  }

  if (initialLoading) {
    return <div className="loading">📡 Chargement des documents...</div>
  }

  if (error && documents.length === 0) {
    return <div className="error">❌ {error}</div>
  }

  return (
    <div className="document-section">
      <div className="section-header">
        <h2 className="section-title">📋 Documents ({documents.length})</h2>
        <button type="button" onClick={() => fetchDocuments({ silent: true })} className="btn-refresh">
          🔄 Rafraîchir
        </button>
      </div>

      {error && <div className="error">⚠️ {error}</div>}

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
                <div
                  className={`doc-status status-${
                    doc.status === 'processing' || extractingId === doc.id ? 'processing' : doc.status
                  }`}
                >
                  {doc.status === 'processing' || extractingId === doc.id
                    ? '⏳ extraction…'
                    : doc.status}
                </div>
              </div>

              <div className="doc-actions">
                {(doc.status === 'uploaded' || doc.status === 'error') && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation()
                      extractDocument(doc.id)
                    }}
                    className="btn btn-success"
                    disabled={extractingId !== null}
                  >
                    {extractingId === doc.id ? '⏳ En cours…' : '🔍 Extraire'}
                  </button>
                )}
                {doc.status === 'processing' && (
                  <button
                    type="button"
                    onClick={(e) => resetDocument(doc.id, e)}
                    className="btn btn-secondary"
                    disabled={extractingId !== null}
                  >
                    ↩ Annuler
                  </button>
                )}
                <button
                  type="button"
                  onClick={deleteDocument}
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
