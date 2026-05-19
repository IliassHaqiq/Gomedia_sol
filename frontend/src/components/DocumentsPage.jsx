import { useState, useEffect, useCallback, useRef } from 'react'
import axios from 'axios'
import {
  FileText,
  Upload,
  RefreshCw,
  Play,
  RotateCcw,
  Loader2,
  X,
  FileSpreadsheet,
} from 'lucide-react'
import './DocumentsPage.css'

const EXTRACT_TIMEOUT_MS = 720000
const POLL_INTERVAL_MS = 8000

const STATUS_LABELS = {
  uploaded: 'En attente',
  processing: 'Extraction…',
  extracted: 'Terminé',
  alimented: 'Alimenté',
  error: 'Erreur',
}

function authHeaders(apiKey) {
  const headers = {}
  if (apiKey) headers.Authorization = `Bearer ${apiKey}`
  return headers
}

function statusBadgeClass(status) {
  if (status === 'uploaded') return 'status-dot status-dot-teal-text'
  if (status === 'processing') return 'status-dot status-dot-magenta-text'
  if (status === 'extracted') return 'status-dot status-dot-lime-text'
  if (status === 'alimented') return 'status-dot status-dot-lime-text'
  return 'status-dot status-dot-magenta-text'
}

function FileIcon({ filename }) {
  const isExcel = filename?.toLowerCase().endsWith('.xlsx')
  const Icon = isExcel ? FileSpreadsheet : FileText
  return <Icon size={20} style={{ color: 'var(--electric-blue)', flexShrink: 0 }} />
}

export default function DocumentsPage({ apiKey }) {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [pendingFiles, setPendingFiles] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const [activeExtractId, setActiveExtractId] = useState(null)
  const [isExtractingAll, setIsExtractingAll] = useState(false)
  const [isAlimentingAll, setIsAlimentingAll] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [toast, setToast] = useState(null)
  const [descriptionLength, setDescriptionLength] = useState(
    () => localStorage.getItem('descriptionLength') || 'medium'
  )

  const toastTimer = useRef(null)

  const showToast = useCallback((message, type = 'info') => {
    setToast({ message, type })
    if (toastTimer.current) clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), 5000)
  }, [])

  const fetchDocuments = useCallback(
    async ({ silent = false } = {}) => {
      if (!silent) setLoading(true)
      setError(null)

      try {
        const res = await axios.get('/api/documents/', {
          headers: authHeaders(apiKey),
        })
        setDocuments(res.data || [])
      } catch (err) {
        const msg = err.response?.data?.detail || 'Impossible de charger les documents'
        setError(msg)
        if (!silent) showToast(msg, 'error')
      } finally {
        if (!silent) setLoading(false)
      }
    },
    [apiKey, showToast]
  )

  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  const hasProcessing = documents.some((d) => d.status === 'processing')

  useEffect(() => {
    if (!hasProcessing && activeExtractId === null) return undefined

    const interval = setInterval(() => {
      fetchDocuments({ silent: true })
    }, POLL_INTERVAL_MS)

    return () => clearInterval(interval)
  }, [hasProcessing, activeExtractId, fetchDocuments])

  const counts = {
    uploaded: documents.filter((d) => d.status === 'uploaded').length,
    processing: documents.filter((d) => d.status === 'processing').length,
    extracted: documents.filter((d) => d.status === 'extracted').length,
    alimented: documents.filter((d) => d.status === 'alimented').length,
    error: documents.filter((d) => d.status === 'error').length,
  }

  const busy =
    isUploading ||
    activeExtractId !== null ||
    isExtractingAll ||
    isAlimentingAll ||
    hasProcessing

  const addFiles = (fileList) => {
    if (!fileList?.length) return

    const allowed = ['.pdf', '.xlsx']

    const incoming = Array.from(fileList).filter((f) =>
      allowed.some((ext) => f.name.toLowerCase().endsWith(ext))
    )

    if (incoming.length < fileList.length) {
      showToast('Seuls les fichiers PDF et XLSX sont acceptés', 'error')
    }

    if (incoming.length) {
      setPendingFiles((prev) => [...prev, ...incoming])
    }
  }

  const removePending = (index) => {
    setPendingFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const uploadPending = async () => {
    if (pendingFiles.length === 0) {
      showToast('Sélectionnez au moins un fichier', 'error')
      return
    }

    setIsUploading(true)

    try {
      const formData = new FormData()
      const isSingle = pendingFiles.length === 1

      if (isSingle) {
        formData.append('file', pendingFiles[0])
      } else {
        pendingFiles.forEach((f) => formData.append('files', f))
      }

      const endpoint = isSingle ? '/api/documents/upload' : '/api/documents/upload-multiple'

      const res = await axios.post(endpoint, formData, {
        headers: {
          ...authHeaders(apiKey),
          'Content-Type': 'multipart/form-data',
        },
      })

      const uploaded = isSingle
        ? 1
        : res.data?.uploaded_count ?? res.data?.documents?.length ?? pendingFiles.length

      const skipped = res.data?.skipped_count ?? 0

      setPendingFiles([])
      await fetchDocuments({ silent: true })

      if (skipped > 0) {
        showToast(`${uploaded} fichier(s) uploadé(s), ${skipped} ignoré(s)`, 'info')
      } else {
        showToast(
          `${uploaded} fichier(s) uploadé(s) — lancez l'extraction ou l'alimentation`,
          'success'
        )
      }
    } catch (err) {
      showToast(err.response?.data?.detail || err.message, 'error')
    } finally {
      setIsUploading(false)
    }
  }

  const extractOne = async (docId) => {
    const doc = documents.find((d) => d.id === docId)

    if (doc?.status === 'processing') {
      showToast('Extraction déjà en cours pour ce document', 'info')
      return
    }

    if (hasProcessing) {
      showToast('Une autre extraction est en cours — patientez', 'info')
      return
    }

    setActiveExtractId(docId)
    showToast('Extraction démarrée (5–12 min selon la longueur)', 'info')

    try {
      const res = await axios.post(
        `/api/documents/${docId}/extract?description_length=${descriptionLength}`,
        {},
        {
          headers: authHeaders(apiKey),
          timeout: EXTRACT_TIMEOUT_MS,
        }
      )

      const n = res.data?.products?.length ?? 0
      showToast(`Extraction terminée — ${n} produit(s) créé(s)`, 'success')
      await fetchDocuments({ silent: true })
    } catch (err) {
      const detail = err.response?.data?.detail
      const msg = typeof detail === 'string' ? detail : err.message

      if (err.response?.status === 409) {
        showToast(msg, 'info')
      } else if (err.code === 'ECONNABORTED') {
        showToast('Délai dépassé — vérifiez les logs serveur ou essayez « Court »', 'error')
      } else {
        showToast(msg, 'error')
      }

      await fetchDocuments({ silent: true })
    } finally {
      setActiveExtractId(null)
    }
  }

  const alimenterOne = async (docId) => {
    if (busy) return

    try {
      await axios.post(
        `/api/documents/${docId}/alimenter`,
        {},
        {
          headers: authHeaders(apiKey),
          timeout: EXTRACT_TIMEOUT_MS,
        }
      )

      showToast('Document alimenté avec succès', 'success')
      await fetchDocuments({ silent: true })
    } catch (err) {
      showToast(err.response?.data?.detail || err.message, 'error')
    }
  }

  const extractAll = async () => {
    if (counts.uploaded === 0) {
      showToast("Aucun document en attente d'extraction", 'info')
      return
    }

    if (busy) {
      showToast('Une opération est déjà en cours', 'info')
      return
    }

    setIsExtractingAll(true)
    showToast(`Extraction de ${counts.uploaded} document(s) en cours…`, 'info')

    try {
      const res = await axios.post(
        `/api/documents/extract-all?description_length=${descriptionLength}`,
        {},
        {
          headers: authHeaders(apiKey),
          timeout: EXTRACT_TIMEOUT_MS * Math.max(counts.uploaded, 1),
        }
      )

      const ok = (res.data?.results || []).filter((r) => r.status === 'success').length
      const fail = (res.data?.results || []).filter((r) => r.status === 'error').length

      showToast(
        `Extraction terminée : ${ok} réussi(s), ${fail} erreur(s)`,
        fail ? 'error' : 'success'
      )

      await fetchDocuments({ silent: true })
    } catch (err) {
      showToast(err.response?.data?.detail || err.message, 'error')
    } finally {
      setIsExtractingAll(false)
    }
  }

  const alimentAll = async () => {
    if (counts.uploaded === 0) {
      showToast('Aucun document à alimenter', 'info')
      return
    }

    if (busy) {
      showToast('Une opération est déjà en cours', 'info')
      return
    }

    if (!confirm('Alimenter tous les documents sans extraction ?')) {
      return
    }

    setIsAlimentingAll(true)
    showToast(`Alimentation de ${counts.uploaded} document(s) en cours…`, 'info')

    try {
      const res = await axios.post(
        '/api/documents/aliment-all',
        {},
        {
          headers: authHeaders(apiKey),
          timeout: EXTRACT_TIMEOUT_MS * Math.max(counts.uploaded, 1),
        }
      )

      const ok = (res.data?.results || []).filter((r) => r.status === 'success').length
      const fail = (res.data?.results || []).filter((r) => r.status === 'error').length

      showToast(
        `Alimentation terminée : ${ok} réussi(s), ${fail} erreur(s)`,
        fail ? 'error' : 'success'
      )

      await fetchDocuments({ silent: true })
    } catch (err) {
      showToast(err.response?.data?.detail || err.message, 'error')
    } finally {
      setIsAlimentingAll(false)
    }
  }

  const resetDoc = async (docId) => {
    try {
      await axios.post(`/api/documents/${docId}/reset`, {}, {
        headers: authHeaders(apiKey),
      })

      showToast('Document réinitialisé — vous pouvez ré-extraire', 'success')
      await fetchDocuments({ silent: true })
    } catch (err) {
      showToast(err.response?.data?.detail || err.message, 'error')
    }
  }

  const handleLengthChange = (value) => {
    setDescriptionLength(value)
    localStorage.setItem('descriptionLength', value)
  }

  return (
    <div className="documents-page">
      <div className="documents-toolbar">
        <div className="documents-toolbar-left">
          <div className="documents-stats">
            <span className="doc-stat-chip doc-stat-chip--pending">
              En attente <strong>{counts.uploaded}</strong>
            </span>

            <span className="doc-stat-chip doc-stat-chip--processing">
              En cours <strong>{counts.processing}</strong>
            </span>

            <span className="doc-stat-chip doc-stat-chip--done">
              Terminés <strong>{counts.extracted}</strong>
            </span>

            <span className="doc-stat-chip doc-stat-chip--done">
              Alimentés <strong>{counts.alimented}</strong>
            </span>

            {counts.error > 0 && (
              <span className="doc-stat-chip doc-stat-chip--error">
                Erreurs <strong>{counts.error}</strong>
              </span>
            )}
          </div>

          <label>
            Longueur
            <select
              className="form-select"
              style={{ marginLeft: '0.5rem', minWidth: '140px' }}
              value={descriptionLength}
              onChange={(e) => handleLengthChange(e.target.value)}
              disabled={busy}
            >
              <option value="short">Court</option>
              <option value="medium">Moyen</option>
              <option value="long">Long</option>
            </select>
          </label>
        </div>

        <div className="documents-toolbar-right">
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => fetchDocuments({ silent: true })}
            disabled={loading}
          >
            <RefreshCw size={16} />
            Actualiser
          </button>

          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={extractAll}
            disabled={busy || counts.uploaded === 0}
          >
            {isExtractingAll ? <Loader2 size={16} className="spin" /> : <Play size={16} />}
            Extraire tout ({counts.uploaded})
          </button>

          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={alimentAll}
            disabled={busy || counts.uploaded === 0}
          >
            {isAlimentingAll ? <Loader2 size={16} className="spin" /> : <Play size={16} />}
            Alimenter tout ({counts.uploaded})
          </button>
        </div>
      </div>

      <section
        className={`documents-upload ${dragActive ? 'is-dragover' : ''}`}
        onDragEnter={(e) => {
          e.preventDefault()
          setDragActive(true)
        }}
        onDragOver={(e) => {
          e.preventDefault()
          setDragActive(true)
        }}
        onDragLeave={(e) => {
          e.preventDefault()
          setDragActive(false)
        }}
        onDrop={(e) => {
          e.preventDefault()
          setDragActive(false)
          addFiles(e.dataTransfer.files)
        }}
      >
        <div className="documents-upload-inner">
          <Upload size={40} className="documents-upload-icon" />

          <div className="documents-upload-text">
            <h3>Déposer des fiches techniques</h3>
            <p>PDF ou Excel (.xlsx) — max 10 Mo par fichier</p>
          </div>

          <label className="btn btn-primary btn-sm" style={{ cursor: 'pointer' }}>
            Parcourir
            <input
              type="file"
              multiple
              accept=".pdf,.xlsx"
              className="documents-upload-input"
              onChange={(e) => {
                addFiles(e.target.files)
                e.target.value = ''
              }}
            />
          </label>
          {pendingFiles.length > 0 && (
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={uploadPending}
              disabled={isUploading}
            >
              {isUploading ? (
                <>
                  <Loader2 size={16} className="spin" /> Envoi…
                </>
              ) : (
                <>
                  <Upload size={16} /> Envoyer {pendingFiles.length} fichier(s)
                </>
              )}
            </button>
          )}
        </div>

        {pendingFiles.length > 0 && (
          <div className="documents-pending-files">
            <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
              Fichiers à envoyer
            </span>
            <ul>
              {pendingFiles.map((file, i) => (
                <li key={`${file.name}-${i}`}>
                  <span title={file.name}>{file.name}</span>
                  <span style={{ color: 'var(--text-tertiary)', flexShrink: 0 }}>
                    {(file.size / 1024).toFixed(0)} Ko
                  </span>
                  <button
                    type="button"
                    className="btn btn-ghost btn-sm"
                    onClick={() => removePending(i)}
                    aria-label="Retirer"
                  >
                    <X size={14} />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <div className="card card-no-shadow documents-table-wrap">
        <div className="card-header card-header-no-border">
          <div>
            <h2 className="card-title">Bibliothèque</h2>
            <p className="card-subtitle">
              {documents.length} document(s) — upload puis extraction via Ollama
            </p>
          </div>
        </div>

        {loading ? (
          <div className="documents-loading">
            <Loader2 size={24} className="spin" />
            Chargement…
          </div>
        ) : error && documents.length === 0 ? (
          <div className="documents-empty">
            <p>{error}</p>
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => fetchDocuments()}>
              Réessayer
            </button>
          </div>
        ) : documents.length === 0 ? (
          <div className="documents-empty">
            <FileText size={48} />
            <p>Aucun document. Déposez un PDF ou un Excel ci-dessus.</p>
          </div>
        ) : (
          <div className="data-table-container table-no-border">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="th-blue">Fichier</th>
                  <th className="th-blue">Statut</th>
                  <th className="th-blue">Date</th>
                  <th className="th-blue" style={{ textAlign: 'right' }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {documents.map((doc) => {
                  const isRowBusy = doc.status === 'processing' || activeExtractId === doc.id
                  const canExtract =
                    (doc.status === 'uploaded' || doc.status === 'error') && !busy
                  const canReset = doc.status === 'processing' && !activeExtractId

                  return (
                    <tr key={doc.id}>
                      <td>
                        <div className="doc-filename-cell">
                          <FileIcon filename={doc.filename} />
                          <span title={doc.filename}>{doc.filename}</span>
                        </div>
                      </td>
                      <td>
                        <span className={statusBadgeClass(doc.status)}>
                          {STATUS_LABELS[doc.status] || doc.status}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-tertiary)', fontSize: '0.875rem' }}>
                        {doc.uploaded_at
                          ? new Date(doc.uploaded_at).toLocaleString('fr-FR', {
                              day: 'numeric',
                              month: 'short',
                              year: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                            })
                          : '—'}
                      </td>
                      <td>
                        <div className="doc-actions-cell">
                          {canExtract && (
                            <button
                              type="button"
                              className="btn btn-primary btn-sm"
                              onClick={() => extractOne(doc.id)}
                              disabled={busy}
                            >
                              {activeExtractId === doc.id ? (
                                <Loader2 size={14} className="spin" />
                              ) : (
                                <Play size={14} />
                              )}
                              Extraire
                            </button>
                          )}

                            {canExtract && (
                              <button
                                type="button"
                                className="btn btn-secondary btn-sm"
                                onClick={() => alimenterOne(doc.id)}
                                disabled={busy}
                              >
                                <Play size={14} />
                                Alimenter
                              </button>
                            )}
                                                      {isRowBusy && doc.status === 'processing' && (
                            <span className="btn btn-ghost btn-sm" style={{ pointerEvents: 'none' }}>
                              <Loader2 size={14} className="spin" /> En cours…
                            </span>
                          )}
                          {canReset && (
                            <button
                              type="button"
                              className="btn btn-ghost btn-sm"
                              onClick={() => resetDoc(doc.id)}
                            >
                              <RotateCcw size={14} />
                              Débloquer
                            </button>
                          )}
                          {doc.status === 'extracted' && (
                            <span style={{ fontSize: '0.8125rem', color: 'var(--text-tertiary)' }}>
                              Voir l’onglet Produits
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {toast && (
        <div role="status" className={`documents-toast documents-toast--${toast.type}`}>
          {toast.message}
        </div>
      )}
    </div>
  )
}
