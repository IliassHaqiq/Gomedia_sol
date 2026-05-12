import { useState, useEffect } from 'react'
import axios from 'axios'

export default function ProductList({ apiKey }) {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedProduct, setSelectedProduct] = useState(null)
  const [showDetail, setShowDetail] = useState(false)

  const fetchProducts = async () => {
    setLoading(true)
    setError(null)

    try {
      const headers = {}
      if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`
      }

      const response = await axios.get('/api/products/', { headers })
      setProducts(response.data || [])
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement des produits')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProducts()
  }, [apiKey])

  const fetchProductDetail = async (productId) => {
    try {
      const headers = {}
      if (apiKey) {
        headers['Authorization'] = `Bearer ${apiKey}`
      }

      const response = await axios.get(`/api/products/${productId}`, { headers })
      setSelectedProduct(response.data)
      setShowDetail(true)
    } catch (err) {
      alert(`❌ Erreur chargement détail: ${err.response?.data?.detail || err.message}`)
    }
  }

  const closeDetail = () => {
    setShowDetail(false)
    setSelectedProduct(null)
  }

  if (loading) {
    return <div className="loading">📡 Chargement des produits...</div>
  }

  if (error) {
    return <div className="error">❌ {error}</div>
  }

  if (showDetail && selectedProduct) {
    return (
      <div className="animate-fade-in">
        <button onClick={closeDetail} className="btn btn-ghost" style={{ marginBottom: '1rem' }}>
          ← Retour à la liste
        </button>

        <div className="card card-no-shadow">
          <div className="card-header card-header-no-border">
            <div>
              <h2 className="card-title">{selectedProduct.ref_produit}</h2>
              <p className="card-subtitle">{selectedProduct.designation || 'Sans désignation'}</p>
            </div>
            <span className="status-dot status-dot-lime-text">Actif</span>
          </div>

          <div className="spec-grid">
            <div className="spec-section">
              <h3>Identification</h3>
              <div className="spec-item">
                <span className="spec-key">Référence:</span>
                <span className="spec-value">{selectedProduct.ref_produit}</span>
              </div>
              <div className="spec-item">
                <span className="spec-key">Désignation:</span>
                <span className="spec-value">{selectedProduct.designation || 'N/A'}</span>
              </div>
              <div className="spec-item">
                <span className="spec-key">Fabricant:</span>
                <span className="spec-value">{selectedProduct.marque || 'N/A'}</span>
              </div>
            </div>

            {selectedProduct.descriptions && (
              <div className="spec-section">
                <h3>Descriptions</h3>
                <div className="spec-item">
                  <span className="spec-key">FR:</span>
                  <span className="spec-value">{selectedProduct.descriptions.descriptif_fr || 'N/A'}</span>
                </div>
                <div className="spec-item">
                  <span className="spec-key">EN:</span>
                  <span className="spec-value">{selectedProduct.descriptions.descriptif_en_specs || 'N/A'}</span>
                </div>
              </div>
            )}

            {selectedProduct.technical_specs && selectedProduct.technical_specs.length > 0 && (
              <div className="spec-section">
                <h3>Spécifications Techniques</h3>
                {selectedProduct.technical_specs.map((spec) => (
                  <div className="spec-item" key={spec.id}>
                    <span className="spec-key">{spec.attribut}:</span>
                    <span className="spec-value">
                      {spec.valeur} {spec.unite ? `(${spec.unite})` : ''}
                    </span>
                  </div>
                ))}
              </div>
            )}

            {selectedProduct.files && selectedProduct.files.length > 0 && (
              <div className="spec-section">
                <h3>Fichiers associés</h3>
                {selectedProduct.files.map((file) => (
                  <div className="spec-item" key={file.id}>
                    <span className="spec-key">Fichier:</span>
                    <span className="spec-value">{file.file_name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      <div className="card card-no-shadow">
        <div className="card-header card-header-no-border">
          <div>
            <h2 className="card-title">Catalogue Produits</h2>
            <p className="card-subtitle">{products.length} produits extraits</p>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button className="btn btn-secondary btn-sm" onClick={fetchProducts}>
              Rafraîchir
            </button>
          </div>
        </div>

        {products.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📦</div>
            <p>Aucun produit trouvé.</p>
            <p>Uploadez et extrayez des documents pour créer des produits.</p>
          </div>
        ) : (
          <div className="data-table-container table-no-border">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="th-blue">Référence</th>
                  <th className="th-blue">Désignation</th>
                  <th className="th-blue">Fabricant</th>
                  <th className="th-blue">Statut</th>
                  <th className="th-blue">Action</th>
                </tr>
              </thead>
              <tbody>
                {products.map((product) => (
                  <tr key={product.id}>
                    <td>
                      <span style={{ fontWeight: 600, color: 'var(--electric-blue)' }}>
                        {product.ref_produit}
                      </span>
                    </td>
                    <td>{product.designation || 'N/A'}</td>
                    <td>{product.marque || 'N/A'}</td>
                    <td>
                      <span className="status-dot status-dot-lime-text">Actif</span>
                    </td>
                    <td>
                      <button
                        className="btn btn-ghost btn-sm"
                        onClick={() => fetchProductDetail(product.id)}
                      >
                        Voir
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
