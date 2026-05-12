import { useState } from 'react'
import axios from 'axios'

export default function UploadFiles({ apiKey }) {
  const [selectedFiles, setSelectedFiles] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [descriptionLength, setDescriptionLength] = useState('medium')

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFiles(Array.from(e.dataTransfer.files))
      e.dataTransfer.clearData()
    }
  }

  const handleFileChange = (e) => {
    if (e.target.files) {
      setSelectedFiles(Array.from(e.target.files))
    }
  }

  const uploadFiles = async () => {
    if (selectedFiles.length === 0) {
      setUploadResult({ type: 'error', message: 'Veuillez sélectionner au moins un fichier' })
      return
    }

    setIsUploading(true)
    setUploadResult(null)

    try {
      const formData = new FormData()
      const isSingle = selectedFiles.length === 1

      if (isSingle) {
        formData.append('file', selectedFiles[0])
      } else {
        selectedFiles.forEach((file) => formData.append('files', file))
      }

      const headers = {}
      if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`
      }

      const endpoint = isSingle ? '/api/documents/upload' : '/api/documents/upload-multiple'
      const url = endpoint

      const response = await axios.post(url, formData, {
        headers: {
          ...headers,
          'Content-Type': 'multipart/form-data',
        },
      })

      setUploadResult({
        type: 'success',
        data: response.data,
        isSingle,
      })

      // Auto-extract after successful upload
      if (isSingle && response.data.document?.id) {
        setTimeout(() => {
          extractDocument(response.data.document.id)
        }, 1000)
      }
    } catch (error) {
      setUploadResult({
        type: 'error',
        message: error.response?.data?.detail || error.message,
      })
    } finally {
      setIsUploading(false)
    }
  }

  const extractDocument = async (documentId) => {
    try {
      const headers = {}
      if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`
      }

      await axios.post(
        `/api/documents/${documentId}/extract?description_length=${descriptionLength}`,
        {},
        { headers }
      )

      setUploadResult((prev) => ({
        ...prev,
        extraction: { type: 'success', message: 'Extraction automatique démarrée' },
      }))
    } catch (error) {
      setUploadResult((prev) => ({
        ...prev,
        extraction: {
          type: 'error',
          message: error.response?.data?.detail || 'Erreur extraction',
        },
      }))
    }
  }

  const extractAll = async () => {
    try {
      const headers = {}
      if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`
      }

      const response = await axios.post(
        `/api/documents/extract-all?description_length=${descriptionLength}`,
        {},
        { headers }
      )

      setUploadResult({
        type: 'success',
        extractAll: response.data,
      })
    } catch (error) {
      setUploadResult({
        type: 'error',
        message: error.response?.data?.detail || 'Erreur extraction batch',
      })
    }
  }

  const removeFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
  }

  return (
    <div className="upload-section">
      <div className="options-section">
        <label htmlFor="descriptionLength">Longueur description :</label>
        <select
          id="descriptionLength"
          value={descriptionLength}
          onChange={(e) => setDescriptionLength(e.target.value)}
          className="select-field"
        >
          <option value="short">Court (200-500 mots)</option>
          <option value="medium">Moyen (500-800 mots)</option>
          <option value="long">Long (800-1300 mots)</option>
        </select>
      </div>

      <div
        className={`upload-card ${dragActive ? 'dragover' : ''}`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
      >
        <label htmlFor="fileInput" className="upload-label">
          <div className="upload-icon">📄</div>
          <div className="upload-text">
            Glissez-déposez vos fichiers ici
          </div>
          <div className="upload-subtext">
            ou cliquez pour sélectionner
          </div>
          <div className="upload-subtext">
            Format supporté : PDF, Excel (.xlsx)
          </div>
        </label>
        <input
          id="fileInput"
          type="file"
          multiple
          accept=".pdf,.xlsx,application/pdf,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          onChange={handleFileChange}
          className="upload-input"
        />

        {selectedFiles.length > 0 && (
          <div className="file-list">
            <h4>Fichiers sélectionnés :</h4>
            {selectedFiles.map((file, index) => (
              <div key={index} className="file-item">
                <span>{file.name} ({(file.size / 1024).toFixed(2)} KB)</span>
                <button
                  onClick={() => removeFile(index)}
                  className="btn-remove"
                  title="Supprimer"
                >
                  🗑️
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="upload-actions">
        <button
          onClick={uploadFiles}
          disabled={isUploading || selectedFiles.length === 0}
          className="btn-upload"
        >
          {isUploading ? '📤 Upload en cours...' : `📤 Upload ${selectedFiles.length} fichier(s)`}
        </button>

        {selectedFiles.length === 0 && (
          <button
            onClick={extractAll}
            disabled={isUploading}
            className="btn-success"
          >
            🔄 Extraire tous les documents
          </button>
        )}
      </div>

      {uploadResult && uploadResult.type === 'success' && (
        <div className="success">✅ Upload réussi !</div>
      )}
      {uploadResult && uploadResult.type === 'error' && (
        <div className="error">❌ Erreur: {uploadResult.message}</div>
      )}
      {uploadResult?.extraction && (
        <div className={uploadResult.extraction.type === 'success' ? 'success' : 'error'}>
          {uploadResult.extraction.type === 'success' ? '✅' : '❌'} {uploadResult.extraction.message}
        </div>
      )}
    </div>
  )
}
