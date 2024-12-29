import React, { useState, useEffect } from 'react';
import { Container, Table, Button, Alert } from 'react-bootstrap';
import { getSharedFiles, downloadFile, deleteFile } from '../services/api';
import './FileManager.css';
import { useSelector } from 'react-redux';

const SharedFiles = () => {
  const { user } = useSelector(state => state.auth);
  const [files, setFiles] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchFiles();
  }, []);

  const fetchFiles = async () => {
    try {
      const data = await getSharedFiles();
      setFiles(data);
    } catch (error) {
      setError('Failed to fetch shared files');
    }
  };

  const handleDownload = async (fileId) => {
    try {
      await downloadFile(fileId);
    } catch (error) {
      if (error.message === 'File no longer exists' || 
          error.message === 'File not found' ||
          error.message === 'File is corrupted or unavailable') {
        await fetchFiles();
      }
      setError(error.message || 'Failed to download file. Please try again.');
    }
  };

  const handleDelete = async (fileId) => {
    if (window.confirm('Are you sure you want to delete this file?')) {
      try {
        await deleteFile(fileId);
        await fetchFiles();
      } catch (error) {
        setError('Failed to delete file');
      }
    }
  };

  return (
    <Container className="file-manager mt-4">
      <h2 className="file-manager-title">Shared Files</h2>
      
      {error && <Alert variant="danger">{error}</Alert>}

      <Table hover className="file-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Size</th>
            <th>Uploaded At</th>
            <th>Owner</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {files.map(file => (
            <tr key={file.id}>
              <td>{file.original_name}</td>
              <td>{Math.round(file.file_size / 1024)} KB</td>
              <td>{new Date(file.uploaded_at).toLocaleString()}</td>
              <td>{file.owner_email}</td>
              <td>
                <div className="d-flex gap-2 justify-content-center">
                  {(file.can_download) && (
                    <Button
                      variant="dark"
                      size="sm"
                      onClick={() => handleDownload(file.id)}
                    >
                      Download
                    </Button>
                  )}
                  {user?.role === 'ADMIN' && (
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleDelete(file.id)}
                    >
                      Delete
                    </Button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Container>
  );
};

export default SharedFiles; 