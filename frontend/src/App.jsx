import { useState, useEffect } from 'react'
import {
  Upload,
  FileText,
  Package,
  BarChart3,
  Settings,
  Search,
  Bell,
  ChevronDown,
  Plus,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertCircle,
  Activity
} from 'lucide-react'
import './styles/index.css'
import UploadFiles from './components/UploadFiles'
import DocumentList from './components/DocumentList'
import SpecificationDetail from './components/SpecificationDetail'
import ProductList from './components/ProductList'
import DocumentGenerator from './components/DocumentGenerator'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const [searchQuery, setSearchQuery] = useState('')
  const [userDropdownOpen, setUserDropdownOpen] = useState(false)
  const [apiKey, setApiKey] = useState(localStorage.getItem('apiKey') || '')
  const [selectedDocumentId, setSelectedDocumentId] = useState(null)

  const navItems = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'documents', label: 'Documents' },
    { id: 'products', label: 'Products' },
    { id: 'generator', label: 'Document Generator' },
    { id: 'analytics', label: 'Analytics' },
    { id: 'settings', label: 'Settings' }
  ]

  const handleSelectDocument = (docId) => {
    setSelectedDocumentId(docId)
  }

  return (
    <div className="App">
      {/* Top Navigation Bar - Dark Charcoal */}
      <nav className="top-nav">
        <div className="nav-left">
          {/* GoMedia Logo */}
          <div className="nav-logo">
            <img
              src="/image/gomedia.png"
              alt="GoMedia"
              className="nav-logo-image"
            />
          </div>

          <div className="nav-links">
            {navItems.map((item) => (
              <button
                key={item.id}
                className={`nav-link ${activeTab === item.id ? 'active' : ''}`}
                onClick={() => setActiveTab(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        <div className="nav-right">
          {/* Dark Charcoal Search Input */}
          <div className="search-wrapper-dark">
            <Search size={18} className="search-icon-dark" />
            <input
              type="text"
              className="search-input-dark"
              placeholder="Search..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Notification Bell with Magenta Dot */}
          <div className="notification-bell">
            <Bell size={20} />
            <span className="notification-dot-magenta"></span>
          </div>

          {/* User Profile with Avatar and Name */}
          <div
            className={`dropdown ${userDropdownOpen ? 'open' : ''}`}
            onClick={() => setUserDropdownOpen(!userDropdownOpen)}
          >
            <div className="user-profile-dark">
              <div className="user-avatar-dark">HI</div>
              <div className="user-info">
                <span className="user-name-dark">Haqiq Iliass</span>
              </div>
              <ChevronDown size={16} className="chevron-down" />
            </div>
            <div className="dropdown-menu">
              <div className="dropdown-item">
                <Settings size={16} />
                <span>Settings</span>
              </div>
              <div className="dropdown-divider"></div>
              <div className="dropdown-item" style={{ color: 'var(--magenta)' }}>
                <span>Sign Out</span>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        <div className="content-section">
          {activeTab === 'dashboard' && <DashboardSection />}
          {activeTab === 'documents' && (
            <DocumentsSection
              apiKey={apiKey}
              selectedDocumentId={selectedDocumentId}
              onSelectDocument={handleSelectDocument}
            />
          )}
          {activeTab === 'products' && <ProductsSection apiKey={apiKey} />}
          {activeTab === 'generator' && <DocumentGeneratorSection />}
          {activeTab === 'analytics' && <AnalyticsSection />}
          {activeTab === 'settings' && <SettingsSection apiKey={apiKey} setApiKey={setApiKey} />}
        </div>
      </main>

      {/* Quick Action Button */}
      <button className="quick-action" title="Quick Upload" onClick={() => setActiveTab('documents')}>
        <Plus size={24} />
      </button>
    </div>
  )
}

// Dashboard Section - Updated with specific KPI modules
function DashboardSection() {
  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Overview of your specification extraction activity</p>
      </div>

      {/* KPI Cards - Sleek integrated modules without box shadows */}
      <div className="stats-grid">
        {/* Total Documents - with chartreuse-lime status dot */}
        <div className="stat-item stat-item-no-shadow">
          <div className="stat-label">Total Documents</div>
          <div className="stat-value">247</div>
          <div className="stat-footer">
            <span className="status-dot-lime"></span>
            <span className="stat-footer-text">+12 this week</span>
          </div>
        </div>

        {/* Products Extracted - with Forest Green progress bar */}
        <div className="stat-item stat-item-no-shadow">
          <div className="stat-label">Products Extracted</div>
          <div className="stat-value">1,842</div>
          <div className="stat-footer">
            <div className="progress-bar-forest">
              <div className="progress-fill-forest" style={{ width: '78%' }}></div>
            </div>
            <span className="stat-footer-text">78% of target</span>
          </div>
        </div>

        {/* Processing Rate - with Teal line chart */}
        <div className="stat-item stat-item-no-shadow">
          <div className="stat-label">Processing Rate</div>
          <div className="stat-value">98.2%</div>
          <div className="stat-footer">
            <svg className="line-chart-teal" viewBox="0 0 100 30" preserveAspectRatio="none">
              <polyline
                points="0,25 20,20 40,22 60,15 80,10 100,5"
                fill="none"
                stroke="var(--teal)"
                strokeWidth="2"
              />
            </svg>
            <span className="stat-footer-text">+2.1% improvement</span>
          </div>
        </div>

        {/* Pending Tasks - with soft grey time icon */}
        <div className="stat-item stat-item-no-shadow">
          <div className="stat-label">Pending Tasks</div>
          <div className="stat-value">12</div>
          <div className="stat-footer">
            <Clock size={16} style={{ color: 'var(--text-tertiary)' }} />
            <span className="stat-footer-text">Awaiting processing</span>
          </div>
        </div>
      </div>

      {/* Recent Activity - Streamlined integrated grid */}
      <div className="card card-no-shadow">
        <div className="card-header card-header-no-border">
          <div>
            <h2 className="card-title">Recent Activity</h2>
            <p className="card-subtitle">Latest document uploads and extractions</p>
          </div>
          <button className="btn btn-secondary btn-sm">View All</button>
        </div>

        <div className="data-table-container table-no-border">
          <table className="data-table">
            <thead>
              <tr>
                <th className="th-blue">Document</th>
                <th className="th-blue">Status</th>
                <th className="th-blue">Products</th>
                <th className="th-blue">Date</th>
                <th className="th-blue">Action</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <FileText size={20} style={{ color: 'var(--electric-blue)' }} />
                    <span style={{ fontWeight: 500 }}>60-1493-21.pdf</span>
                  </div>
                </td>
                <td>
                  <span className="status-dot status-dot-lime-text">Completed</span>
                </td>
                <td>3</td>
                <td>Today, 2:34 PM</td>
                <td>
                  <button className="btn btn-ghost btn-sm">View</button>
                </td>
              </tr>
              <tr>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <FileText size={20} style={{ color: 'var(--electric-blue)' }} />
                    <span style={{ fontWeight: 500 }}>UM121.pdf</span>
                  </div>
                </td>
                <td>
                  <span className="status-dot status-dot-magenta-text">Processing</span>
                </td>
                <td>—</td>
                <td>Today, 1:15 PM</td>
                <td>
                  <button className="btn btn-ghost btn-sm">View</button>
                </td>
              </tr>
              <tr>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <FileText size={20} style={{ color: 'var(--electric-blue)' }} />
                    <span style={{ fontWeight: 500 }}>TCS_DAT_71.98.2005.pdf</span>
                  </div>
                </td>
                <td>
                  <span className="status-dot status-dot-lime-text">Completed</span>
                </td>
                <td>5</td>
                <td>Yesterday</td>
                <td>
                  <button className="btn btn-ghost btn-sm">View</button>
                </td>
              </tr>
              <tr>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <FileText size={20} style={{ color: 'var(--electric-blue)' }} />
                    <span style={{ fontWeight: 500 }}>TLP Pro 725C.pdf</span>
                  </div>
                </td>
                <td>
                  <span className="status-dot status-dot-lime-text">Completed</span>
                </td>
                <td>1</td>
                <td>Jan 12, 2024</td>
                <td>
                  <button className="btn btn-ghost btn-sm">View</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// Documents Section - Now with real functionality
function DocumentsSection({ apiKey, selectedDocumentId, onSelectDocument }) {
  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1 className="page-title">Documents</h1>
        <p className="page-subtitle">Upload and manage your technical specification documents</p>
      </div>

      <div className="grid grid-2" style={{ gap: '2rem' }}>
        {/* Left Column - Upload and Document List */}
        <div>
          {/* Upload Zone - Using real component */}
          <UploadFiles apiKey={apiKey} />

          {/* Document List - Using real component */}
          <DocumentList
            apiKey={apiKey}
            onSelectDocument={onSelectDocument}
            selectedDocumentId={selectedDocumentId}
          />
        </div>

        {/* Right Column - Specification Detail */}
        <div>
          {selectedDocumentId ? (
            <SpecificationDetail
              apiKey={apiKey}
              documentId={selectedDocumentId}
            />
          ) : (
            <div className="card card-no-shadow">
              <div className="empty-state">
                <div className="empty-icon">
                  <FileText size={64} />
                </div>
                <p className="empty-title">No Document Selected</p>
                <p className="empty-description">
                  Select a document from the list to view its specifications and extracted data.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Products Section - Now with real functionality
function ProductsSection({ apiKey }) {
  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1 className="page-title">Products</h1>
        <p className="page-subtitle">Browse and manage extracted product specifications</p>
      </div>

      <ProductList apiKey={apiKey} />
    </div>
  )
}

// Document Generator Section
function DocumentGeneratorSection() {
  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1 className="page-title">Document Generator</h1>
        <p className="page-subtitle">Generate A&E specifications and datasheet ZIPs from product data</p>
      </div>

      <DocumentGenerator />
    </div>
  )
}

// Analytics Section
function AnalyticsSection() {
  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1 className="page-title">Analytics</h1>
        <p className="page-subtitle">Insights and trends from your extraction data</p>
      </div>

      <div className="grid grid-2">
        <div className="card card-no-shadow">
          <div className="card-header card-header-no-border">
            <div>
              <h2 className="card-title">Extraction Trends</h2>
              <p className="card-subtitle">Monthly document processing volume</p>
            </div>
          </div>
          <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-tertiary)' }}>
            <div style={{ textAlign: 'center' }}>
              <BarChart3 size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
              <p>Chart visualization coming soon</p>
            </div>
          </div>
        </div>

        <div className="card card-no-shadow">
          <div className="card-header card-header-no-border">
            <div>
              <h2 className="card-title">Product Categories</h2>
              <p className="card-subtitle">Distribution by manufacturer</p>
            </div>
          </div>
          <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-tertiary)' }}>
            <div style={{ textAlign: 'center' }}>
              <Package size={48} style={{ marginBottom: '1rem', opacity: 0.5 }} />
              <p>Chart visualization coming soon</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Settings Section - Now with real API key management
function SettingsSection({ apiKey, setApiKey }) {
  const [localApiKey, setLocalApiKey] = useState(apiKey)
  const [apiEndpoint, setApiEndpoint] = useState(localStorage.getItem('apiEndpoint') || 'https://integrate.api.nvidia.com/v1')
  const [descriptionLength, setDescriptionLength] = useState(localStorage.getItem('descriptionLength') || 'medium')
  const [notificationEmail, setNotificationEmail] = useState(localStorage.getItem('notificationEmail') || '')

  const handleSave = () => {
    localStorage.setItem('apiKey', localApiKey)
    localStorage.setItem('apiEndpoint', apiEndpoint)
    localStorage.setItem('descriptionLength', descriptionLength)
    localStorage.setItem('notificationEmail', notificationEmail)
    setApiKey(localApiKey)
    alert('Settings saved successfully!')
  }

  const handleCancel = () => {
    setLocalApiKey(apiKey)
    setApiEndpoint(localStorage.getItem('apiEndpoint') || 'https://integrate.api.nvidia.com/v1')
    setDescriptionLength(localStorage.getItem('descriptionLength') || 'medium')
    setNotificationEmail(localStorage.getItem('notificationEmail') || '')
  }

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Configure your extraction preferences</p>
      </div>

      <div className="card card-no-shadow" style={{ maxWidth: '600px' }}>
        <div className="card-header card-header-no-border">
          <h2 className="card-title">API Configuration</h2>
        </div>

        <div className="form-group">
          <label className="form-label">NVIDIA NIM API Key</label>
          <input
            type="password"
            className="form-input"
            placeholder="Enter your API key"
            value={localApiKey}
            onChange={(e) => setLocalApiKey(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label className="form-label">API Endpoint</label>
          <input
            type="text"
            className="form-input"
            value={apiEndpoint}
            onChange={(e) => setApiEndpoint(e.target.value)}
          />
        </div>

        <div className="card-header card-header-no-border" style={{ marginTop: '2rem' }}>
          <h2 className="card-title">Extraction Preferences</h2>
        </div>

        <div className="form-group">
          <label className="form-label">Default Description Length</label>
          <select
            className="form-select"
            value={descriptionLength}
            onChange={(e) => setDescriptionLength(e.target.value)}
          >
            <option value="short">Court (200-500 mots)</option>
            <option value="medium">Moyen (500-800 mots)</option>
            <option value="long">Long (800-1300 mots)</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Notification Email</label>
          <input
            type="email"
            className="form-input"
            placeholder="your@email.com"
            value={notificationEmail}
            onChange={(e) => setNotificationEmail(e.target.value)}
          />
        </div>

        <div style={{ marginTop: '2rem', display: 'flex', gap: '0.75rem' }}>
          <button className="btn btn-primary" onClick={handleSave}>Save Changes</button>
          <button className="btn btn-ghost" onClick={handleCancel}>Cancel</button>
        </div>
      </div>
    </div>
  )
}

export default App
