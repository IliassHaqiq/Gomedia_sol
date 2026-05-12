# Gomedia Frontend - React Application

Web application React for Gomedia IA Specifications API extraction service.

## 🎨 Design

- **Color Palette**: Green (#2ecc71), Blue (#3498db), White (#ffffff)
- **Style**: Modern, clean, user-friendly
- **Responsive**: Works on desktop and tablet

## ✨ Features

### 📤 Upload Section
- **Single file upload**: Drag & drop or click to select
- **Multiple files upload**: Batch processing
- **File validation**: Size (10MB), type (PDF/Excel)
- **Drag & drop**: Visual feedback
- **Auto-extraction**: Automatic spec extraction after upload

### 📋 Documents Management
- **List all documents**: Real-time refresh
- **Status tracking**: uploaded → extracted → validated
- **One-click extraction**: Extract specs from uploaded docs
- **Document selection**: View specifications

### 📊 Specifications Viewer
- **Structured data display**: Technical specs organized
- **Edit & validate**: Manual correction capability
- **Export to text**: Download specifications
- **Bilingual**: French & English descriptions

### ❤️ Health Monitoring
- **API health**: Check if API is running
- **Database status**: Verify PostgreSQL connection
- **Ollama service**: Check LLM service availability
- **Auto-refresh**: Updates every 30 seconds

## 🚀 Installation

### Prerequisites
- Node.js 18+ (Download from [nodejs.org](https://nodejs.org))
- Backend API running on http://localhost:8000

### Steps

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   # or
   yarn install
   ```

2. **Configure API (optional)**
   - Backend URL is hardcoded to `http://localhost:8000`
   - Edit `vite.config.js` if needed

3. **Start development server**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

4. **Open browser**
   - Navigate to http://localhost:3000

## 📦 Dependencies

- **React 18**: UI framework
- **React DOM**: DOM rendering
- **Axios**: HTTP client for API calls
- **Vite**: Build tool & dev server

## 🎯 Usage

### Upload Files
1. Go to "📤 Upload" tab
2. Drag & drop files or click to select
3. Choose description length (short/medium/long)
4. Click "Upload"

### View Documents
1. Go to "📋 Documents" tab
2. Click on a document to view its specifications
3. Use "🔍 Extraire" button to extract specs

### Health Check
1. Go to "❤️ Health" tab
2. View real-time status of all services
3. Click "🔍 Vérifier" to manual refresh

### API Authentication
1. Click "Clé API" field
2. Enter your API key (if configured)
3. Click "💾 Enregistrer"

## 🔧 Development

### Project Structure
```
frontend/
├── package.json         # Dependencies & scripts
├── vite.config.js       # Build configuration
├── index.html           # Main HTML
└── src/
    ├── main.jsx         # App entry point
    ├── App.jsx          # Main component
    ├── styles/
    │   └── App.css      # Global styles
    └── components/
        ├── UploadFiles.jsx         # File upload
        ├── DocumentList.jsx        # Documents list
        ├── SpecificationDetail.jsx # Spec details
        └── HealthCheck.jsx         # Health monitoring
```

### Commands

```bash
npm run dev      # Start dev server (port 3000)
npm run build    # Build for production
npm run preview  # Preview production build
```

## 🔌 API Integration

The frontend automatically connects to:
- **Upload**: `POST http://localhost:8000/documents/upload`
- **Multiple Upload**: `POST http://localhost:8000/documents/upload-multiple`
- **Extract**: `POST http://localhost:8000/documents/{id}/extract`
- **Extract All**: `POST http://localhost:8000/documents/extract-all`
- **Documents List**: `GET http://localhost:8000/documents/`
- **Specifications**: `GET http://localhost:8000/specifications/`
- **Health Check**: `GET http://localhost:8000/health/*`

## 🎨 Styling

### Color Palette
- **Primary Green**: `#2ecc71` (success, buttons)
- **Primary Blue**: `#3498db` (links, headers)
- **White**: `#ffffff` (background, cards)
- **Dark Green**: `#27ae60` (hover states)
- **Dark Blue**: `#2980b9` (active states)
- **Light Green**: `#d5f5e3` (success backgrounds)
- **Light Blue**: `#d6eaf8` (info backgrounds)
- **Gray**: `#95a5a6` (text secondary)
- **Light Gray**: `#ecf0f1` (borders, backgrounds)

### Components
- **Cards**: White background, subtle shadows
- **Buttons**: Rounded corners, hover effects
- **Forms**: Clean inputs with focus states
- **Alerts**: Colored left borders (success/error/warning)

## 🐛 Troubleshooting

### CORS Errors
- Ensure backend CORS is configured
- Check `ALLOWED_ORIGINS` in backend `.env`

### Connection Refused
- Verify backend is running on port 8000
- Check health status in "❤️ Health" tab

### File Upload Errors
- Max file size: 10MB
- Allowed types: PDF, Excel (.xlsx)
- Check file MIME type

### API Authentication
- If API key required, enter it in header field
- Check `API_KEY` environment variable on backend

### Build Errors
- Clear cache: `rm -rf node_modules && npm install`
- Update Node.js to latest LTS

## 📱 Responsive Design

- **Desktop**: Full layout with sidebar
- **Tablet**: Stacked components
- **Mobile**: Single column, touch-optimized buttons

## 🌟 Enhancements (Future)

- [ ] Dark mode toggle
- [ ] Additional export formats (PDF, Excel)
- [ ] Real-time notifications (WebSocket)
- [ ] Advanced search & filtering
- [ ] Batch operations
- [ ] User authentication
- [ ] Drag & drop reordering

## 📄 License

MIT License - Same as backend

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 🆘 Support

For issues or questions:
- Frontend: Create issue in repo
- API: Check backend logs
- General: Coordinate with backend team

---

**Last Updated**: 13 April 2026
**Version**: 1.0.0
**Maintained by**: Iliass
