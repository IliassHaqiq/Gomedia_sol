import { useState, useEffect } from 'react'
import './ProductManager.css'

function ProductManager({ apiKey }) {
  const [products, setProducts] = useState([])
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('list')

  // Fetch products
  const fetchProducts = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('http://localhost:8000/products/')
      if (!response.ok) throw new Error('Failed to fetch products')
      const data = await response.json()
      setProducts(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Fetch product details
  const fetchProductDetails = async (productId) => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`http://localhost:8000/products/${productId}`)
      if (!response.ok) throw new Error('Failed to fetch product details')
      const data = await response.json()
      setSelectedProduct(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // Generate description
  const generateDescription = async (productId, length) => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(
        `http://localhost:8000/products/${productId}/description/generate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ length }),
        }
      )
      if (!response.ok) throw new Error('Failed to generate description')
      const data = await response.json()

      // Refresh product details
      await fetchProductDetails(productId)

      return data
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  // Add technical spec
  const addTechnicalSpec = async (productId, spec) => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(
        `http://localhost:8000/products/${productId}/specs`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(spec),
        }
      )
      if (!response.ok) throw new Error('Failed to add technical spec')

      // Refresh product details
      await fetchProductDetails(productId)

      return await response.json()
    } catch (err) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  // Delete technical spec
  const deleteTechnicalSpec = async (specId) => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(
        `http://localhost:8000/products/specs/${specId}`,
        {
          method: 'DELETE',
        }
      )
      if (!response.ok) throw new Error('Failed to delete technical spec')

      // Refresh product details
      if (selectedProduct) {
        await fetchProductDetails(selectedProduct.id)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProducts()
  }, [])

  return (
    <div className="product-manager">
      <div className="product-header">
        <h2>📦 Gestion des Produits</h2>
        <button onClick={fetchProducts} className="btn-refresh" disabled={loading}>
          🔄 {loading ? 'Chargement...' : 'Actualiser'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      <div className="product-layout">
        {/* Product List */}
        <div className="product-list">
          <h3>Liste des Produits ({products.length})</h3>
          {products.length === 0 ? (
            <div className="empty-state">
              <p>Aucun produit trouvé</p>
              <small>Créez un produit pour commencer</small>
            </div>
          ) : (
            <ul className="product-items">
              {products.map((product) => (
                <li
                  key={product.id}
                  className={`product-item ${selectedProduct?.id === product.id ? 'active' : ''}`}
                  onClick={() => {
                    setSelectedProduct(null)
                    fetchProductDetails(product.id)
                  }}
                >
                  <div className="product-item-header">
                    <span className="product-ref">{product.ref_produit}</span>
                    {product.marque && <span className="product-brand">{product.marque}</span>}
                  </div>
                  {product.designation && (
                    <div className="product-designation">{product.designation}</div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Product Details */}
        <div className="product-details">
          {selectedProduct ? (
            <ProductDetail
              product={selectedProduct}
              onGenerateDescription={generateDescription}
              onAddSpec={addTechnicalSpec}
              onDeleteSpec={deleteTechnicalSpec}
              loading={loading}
            />
          ) : (
            <div className="empty-state">
              <p>👈 Sélectionnez un produit pour voir les détails</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function ProductDetail({ product, onGenerateDescription, onAddSpec, onDeleteSpec, loading }) {
  const [newSpec, setNewSpec] = useState({ attribut: '', valeur: '', unite: '' })
  const [showSpecForm, setShowSpecForm] = useState(false)

  const handleAddSpec = async (e) => {
    e.preventDefault()
    if (!newSpec.attribut || !newSpec.valeur) return

    try {
      await onAddSpec(product.id, newSpec)
      setNewSpec({ attribut: '', valeur: '', unite: '' })
      setShowSpecForm(false)
    } catch (err) {
      console.error('Failed to add spec:', err)
    }
  }

  return (
    <div className="product-detail">
      <div className="detail-header">
        <h3>{product.ref_produit}</h3>
        {product.marque && <span className="brand-badge">{product.marque}</span>}
      </div>

      {product.designation && (
        <div className="detail-section">
          <h4>Désignation</h4>
          <p>{product.designation}</p>
        </div>
      )}

      {/* Descriptions */}
      <div className="detail-section">
        <div className="section-header">
          <h4>📝 Descriptions</h4>
          <div className="description-actions">
            <button
              onClick={() => onGenerateDescription(product.id, 'short')}
              disabled={loading}
              className="btn-desc btn-short"
              title="Générer description courte"
            >
              Court
            </button>
            <button
              onClick={() => onGenerateDescription(product.id, 'medium')}
              disabled={loading}
              className="btn-desc btn-medium"
              title="Générer description moyenne"
            >
              Moyen
            </button>
            <button
              onClick={() => onGenerateDescription(product.id, 'long')}
              disabled={loading}
              className="btn-desc btn-long"
              title="Générer description longue"
            >
              Long
            </button>
          </div>
        </div>

        {product.descriptions ? (
          <div className="descriptions-content">
            {product.descriptions.descriptif_fr && (
              <div className="description-box">
                <h5>🇫🇷 Français</h5>
                <p>{product.descriptions.descriptif_fr}</p>
                {product.descriptions.last_edited_by_human && (
                  <span className="edited-badge">✏️ Modifié manuellement</span>
                )}
              </div>
            )}
            {product.descriptions.descriptif_en_specs && (
              <div className="description-box">
                <h5>🇬🇧 English</h5>
                <p>{product.descriptions.descriptif_en_specs}</p>
              </div>
            )}
          </div>
        ) : (
          <p className="no-description">Aucune description générée</p>
        )}
      </div>

      {/* Technical Specs */}
      <div className="detail-section">
        <div className="section-header">
          <h4>⚙️ Spécifications Techniques ({product.technical_specs?.length || 0})</h4>
          <button
            onClick={() => setShowSpecForm(!showSpecForm)}
            className="btn-add-spec"
          >
            {showSpecForm ? '✕' : '+'}
          </button>
        </div>

        {showSpecForm && (
          <form onSubmit={handleAddSpec} className="spec-form">
            <input
              type="text"
              placeholder="Attribut (ex: Tension)"
              value={newSpec.attribut}
              onChange={(e) => setNewSpec({ ...newSpec, attribut: e.target.value })}
              required
            />
            <input
              type="text"
              placeholder="Valeur (ex: 230)"
              value={newSpec.valeur}
              onChange={(e) => setNewSpec({ ...newSpec, valeur: e.target.value })}
              required
            />
            <input
              type="text"
              placeholder="Unité (ex: V)"
              value={newSpec.unite}
              onChange={(e) => setNewSpec({ ...newSpec, unite: e.target.value })}
            />
            <button type="submit" disabled={loading}>
              Ajouter
            </button>
          </form>
        )}

        {product.technical_specs && product.technical_specs.length > 0 ? (
          <table className="specs-table">
            <thead>
              <tr>
                <th>Attribut</th>
                <th>Valeur</th>
                <th>Unité</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {product.technical_specs.map((spec) => (
                <tr key={spec.id}>
                  <td>{spec.attribut}</td>
                  <td>{spec.valeur}</td>
                  <td>{spec.unite || '-'}</td>
                  <td>
                    <button
                      onClick={() => onDeleteSpec(spec.id)}
                      className="btn-delete"
                      disabled={loading}
                    >
                      🗑️
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="no-specs">Aucune spécification technique</p>
        )}
      </div>

      {/* Files */}
      {product.files && product.files.length > 0 && (
        <div className="detail-section">
          <h4>📁 Fichiers ({product.files.length})</h4>
          <ul className="files-list">
            {product.files.map((file) => (
              <li key={file.id}>
                📄 {file.file_name}
                <small className="file-date">
                  {new Date(file.created_at).toLocaleDateString('fr-FR')}
                </small>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default ProductManager