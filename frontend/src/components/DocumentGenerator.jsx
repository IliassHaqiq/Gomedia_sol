import React, { useState } from 'react';
import './DocumentGenerator.css';

const DocumentGenerator = () => {
  const [projectName, setProjectName] = useState('');
  const [excelFile, setExcelFile] = useState(null);
  const [partNumbers, setPartNumbers] = useState('');
  const [mode, setMode] = useState('excel'); // 'excel' or 'manual'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setExcelFile(file);
      setError('');
    }
  };

  const handleGenerateAESpecs = async () => {
    if (!projectName.trim()) {
      setError('Project name is required');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const formData = new FormData();
      formData.append('project_name', projectName);

      if (mode === 'excel') {
        if (!excelFile) {
          setError('Please select an Excel file');
          setLoading(false);
          return;
        }
        formData.append('excel', excelFile);

        const response = await fetch('http://localhost:8000/documents-generation/ae-specs', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to generate document');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${projectName}_A&E_Specs.docx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        setSuccess('A&E Specs document generated successfully!');
      } else {
        const parts = partNumbers.split('\n').map(p => p.trim()).filter(p => p);
        if (parts.length === 0) {
          setError('Please enter at least one part number');
          setLoading(false);
          return;
        }

        const response = await fetch('http://localhost:8000/documents-generation/ae-specs/manual', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            project_name: projectName,
            parts: parts,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to generate document');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${projectName}_A&E_Specs.docx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        setSuccess('A&E Specs document generated successfully!');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateDatasheetZip = async () => {
    if (!projectName.trim()) {
      setError('Project name is required');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      if (mode === 'excel') {
        if (!excelFile) {
          setError('Please select an Excel file');
          setLoading(false);
          return;
        }

        const formData = new FormData();
        formData.append('project_name', projectName);
        formData.append('excel', excelFile);

        const response = await fetch('http://localhost:8000/documents-generation/datasheet-zip', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to generate ZIP');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${projectName}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        setSuccess('Datasheet ZIP generated successfully!');
      } else {
        const parts = partNumbers.split('\n').map(p => p.trim()).filter(p => p);
        if (parts.length === 0) {
          setError('Please enter at least one part number');
          setLoading(false);
          return;
        }

        const response = await fetch('http://localhost:8000/documents-generation/datasheet-zip/manual', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            project_name: projectName,
            parts: parts,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to generate ZIP');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${projectName}.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        setSuccess('Datasheet ZIP generated successfully!');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="document-generator">
      <h2>Document Generator</h2>

      <div className="mode-selector">
        <button
          className={`mode-btn ${mode === 'excel' ? 'active' : ''}`}
          onClick={() => setMode('excel')}
        >
          Excel Upload
        </button>
        <button
          className={`mode-btn ${mode === 'manual' ? 'active' : ''}`}
          onClick={() => setMode('manual')}
        >
          Manual Entry
        </button>
      </div>

      <div className="form-group">
        <label htmlFor="projectName">Project Name *</label>
        <input
          type="text"
          id="projectName"
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          placeholder="Enter project name"
        />
      </div>

      {mode === 'excel' ? (
        <div className="form-group">
          <label htmlFor="excelFile">Excel File *</label>
          <input
            type="file"
            id="excelFile"
            accept=".xlsx,.xls"
            onChange={handleFileChange}
          />
          {excelFile && (
            <div className="file-info">
              Selected: {excelFile.name}
            </div>
          )}
          <div className="help-text">
            Excel file must contain columns: reference, N prix, designation
          </div>
        </div>
      ) : (
        <div className="form-group">
          <label htmlFor="partNumbers">Part Numbers *</label>
          <textarea
            id="partNumbers"
            value={partNumbers}
            onChange={(e) => setPartNumbers(e.target.value)}
            placeholder="Enter part numbers (one per line)"
            rows={5}
          />
          <div className="help-text">
            Enter one part number per line
          </div>
        </div>
      )}

      <div className="button-group">
        <button
          className="btn btn-primary"
          onClick={handleGenerateAESpecs}
          disabled={loading}
        >
          {loading ? 'Generating...' : 'Generate A&E Specs'}
        </button>
        <button
          className="btn btn-secondary"
          onClick={handleGenerateDatasheetZip}
          disabled={loading}
        >
          {loading ? 'Generating...' : 'Generate Datasheet ZIP'}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}
    </div>
  );
};

export default DocumentGenerator;
