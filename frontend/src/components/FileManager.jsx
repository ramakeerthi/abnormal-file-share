import React, { useState, useEffect } from 'react';
import { Container, Table, Button, Form, Alert } from 'react-bootstrap';
import { uploadFile, downloadFile, getFiles } from '../services/api';
import './FileManager.css';

const FileManager = () => {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      const data = await getFiles();
      setFiles(data);
    } catch (error) {
      setError('Failed to fetch files');
    }
  };

  const handleFileSelect = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a file');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      await uploadFile(formData);
      await fetchFiles();
      setSelectedFile(null);
      e.target.reset();
    } catch (error) {
      setError('Failed to upload file');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (fileId) => {
    try {
      const response = await downloadFile(fileId);
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'download';
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(url);
      link.remove();
    } catch (error) {
      console.error('Download error:', error);
      setError('Failed to download file');
    }
  };

  return (
    <Container className="file-manager mt-4">
      <h2 className="file-manager-title">File Manager</h2>
      
      {error && <Alert variant="danger">{error}</Alert>}
      
      <Form onSubmit={handleUpload} className="upload-form mb-4">
        <Form.Group>
          <Form.Label>Upload File</Form.Label>
          <div className="d-flex">
            <Form.Control
              type="file"
              onChange={handleFileSelect}
              className="me-2"
            />
            <Button 
              type="submit" 
              variant="dark" 
              disabled={loading}
            >
              {loading ? 'Uploading...' : 'Upload'}
            </Button>
          </div>
        </Form.Group>
      </Form>

      <Table hover className="file-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Size</th>
            <th>Uploaded At</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {files.map(file => (
            <tr key={file.id}>
              <td>{file.original_name}</td>
              <td>{Math.round(file.file_size / 1024)} KB</td>
              <td>{new Date(file.uploaded_at).toLocaleString()}</td>
              <td>
                {file.is_owner && (
                  <Button
                    variant="dark"
                    size="sm"
                    onClick={() => handleDownload(file.id)}
                  >
                    Download
                  </Button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Container>
  );
};

export default FileManager; 