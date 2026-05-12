import { useState, useEffect } from 'react'
import axios from 'axios'

export default function SpecificationDetail({ apiKey, documentId }) {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [editingProduct, setEditingProduct] = useState(null)
  const [editForm, setEditForm] = useState({})

  const fetchProducts = async () => {
    try {
      const headers = {}
      if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`
      }

      const response = await axios.get(
        `/api/products/`,
        { headers }
      )

      setProducts(response.data || [])
      setLoading(false)
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur chargement produits')
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProducts()
  }, [apiKey])

  const validateProduct = async (productId, updates) => {
    try {
      const headers = {}
      if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`
      }

      const response = await axios.put(
        `/api/products/${productId}`,
        updates,
        { headers }
      )

      setProducts(products =>
        products.map(product => product.id === productId ? response.data : product)
      )

      setEditingProduct(null)
      setEditForm({})
      alert('✅ Produit mis à jour !')
    } catch (err) {
      alert(`❌ Erreur mise à jour: ${err.response?.data?.detail || err.message}`)
    }
  }

  const startEdit = (product) => {
    setEditingProduct(product.id)
    setEditForm({
      ref_produit: product.ref_produit || '',
      marque: product.marque || '',
      designation: product.designation || '',
    })
  }

  const cancelEdit = () => {
    setEditingProduct(null)
    setEditForm({})
  }

  const saveEdit = (productId) => {
    validateProduct(productId, { ...editForm })
  }

  const exportProduct = (product) => {
    const content = `
============== FICHE TECHNIQUE PRODUIT ==============
Référence: ${product.ref_produit}
Désignation: ${product.designation}
Fabricant: ${product.marque}

STATUT: Actif
====================================================
    `.trim()

    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `product_${product.id}_${product.ref_produit}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return <div className="loading">🔍 Chargement des produits...</div>
  }

  if (error) {
    return <div className="error">❌ {error}</div>
  }

  if (products.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📊</div>
        <p>Aucun produit trouvé.</p>
        <p>Utilisez le bouton "Extraire" dans la liste des documents.</p>
      </div>
    )
  }

  return (
    <div className="specifications-section">
      {products.map((product) => (
        <div key={product.id} className="spec-detail">
          <div className="spec-header">
            <span className="spec-title">Produit #{product.id}</span>
            <span className={`validation-badge validation-validated`}>
              Actif
            </span>
          </div>

          <div className="spec-grid">
            <div className="spec-section">
              <h3>Identification</h3>
              <div className="spec-item">
                <span className="spec-key">Référence:</span>
                {editingProduct === product.id ? (
                  <input
                    type="text"
                    value={editForm.ref_produit}
                    onChange={(e) => setEditForm({ ...editForm, ref_produit: e.target.value })}
                    className="edit-input"
                  />
                ) : (
                  <span className="spec-value">{product.ref_produit || 'N/A'}</span>
                )}
              </div>
              <div className="spec-item">
                <span className="spec-key">Désignation:</span>
                {editingProduct === product.id ? (
                  <input
                    type="text"
                    value={editForm.designation}
                    onChange={(e) => setEditForm({ ...editForm, designation: e.target.value })}
                    className="edit-input"
                  />
                ) : (
                  <span className="spec-value">{product.designation || 'N/A'}</span>
                )}
              </div>
              <div className="spec-item">
                <span className="spec-key">Fabricant:</span>
                {editingProduct === product.id ? (
                  <input
                    type="text"
                    value={editForm.marque}
                    onChange={(e) => setEditForm({ ...editForm, marque: e.target.value })}
                    className="edit-input"
                  />
                ) : (
                  <span className="spec-value">{product.marque || 'N/A'}</span>
                )}
              </div>
            </div>

            <div className="spec-section">
              <h3>Informations</h3>
              <div className="spec-item">
                <span className="spec-key">Créé le:</span>
                <span className="spec-value">
                  {product.created_at ? new Date(product.created_at).toLocaleDateString() : 'N/A'}
                </span>
              </div>
              <div className="spec-item">
                <span className="spec-key">Mis à jour:</span>
                <span className="spec-value">
                  {product.updated_at ? new Date(product.updated_at).toLocaleDateString() : 'N/A'}
                </span>
              </div>
            </div>
          </div>

          <div className="doc-actions" style={{ marginTop: '1.5rem' }}>
            {editingProduct === product.id ? (
              <>
                <button
                  onClick={() => saveEdit(product.id)}
                  className="btn btn-success"
                >
                  💾 Enregistrer
                </button>
                <button
                  onClick={cancelEdit}
                  className="btn btn-secondary"
                >
                  ❌ Annuler
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => startEdit(product)}
                  className="btn btn-primary"
                >
                  ✏️ Éditer
                </button>
                <button
                  onClick={() => exportProduct(product)}
                  className="btn btn-success"
                >
                  📄 Exporter
                </button>
              </>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
