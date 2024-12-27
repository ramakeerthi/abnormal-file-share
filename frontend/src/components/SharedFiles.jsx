import React, { useState, useEffect } from 'react';
import { Container, Table, Button, Alert, Modal, Form } from 'react-bootstrap';
import { getSharedFiles, downloadFile, deleteFile, shareFile } from '../services/api';
import './FileManager.css';

const SharedFiles = () => {
  const [files, setFiles] = useState([]);
  const [error, setError] = useState('');
  const [showShareModal, setShowShareModal] = useState(false);
  const [selectedFileId, setSelectedFileId] = useState(null);
  const [userEmailToShare, setUserEmailToShare] = useState('');

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
      console.error('Download error:', error);
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

  const handleShare = async (fileId) => {
    setSelectedFileId(fileId);
    setShowShareModal(true);
  };

  const handleShareSubmit = async () => {
    try {
      await shareFile(selectedFileId, userEmailToShare);
      setShowShareModal(false);
      setUserEmailToShare('');
      setError('');
    } catch (error) {
      if (error.response?.data?.error) {
        setError(error.response.data.error);
      } else {
        setError('Failed to share file');
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
                <div className="d-flex gap-2">
                  <Button
                    variant="dark"
                    size="sm"
                    onClick={() => handleDownload(file.id)}
                  >
                    Download
                  </Button>
                  {file.can_manage && (
                    <>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => handleDelete(file.id)}
                      >
                        Delete
                      </Button>
                      <Button
                        variant="info"
                        size="sm"
                        onClick={() => handleShare(file.id)}
                      >
                        Share
                      </Button>
                    </>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      <Modal show={showShareModal} onHide={() => setShowShareModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Share File</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {error && <Alert variant="danger">{error}</Alert>}
          <Form>
            <Form.Group>
              <Form.Label>User Email</Form.Label>
              <Form.Control
                type="email"
                value={userEmailToShare}
                onChange={(e) => setUserEmailToShare(e.target.value)}
                placeholder="Enter user email to share with"
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowShareModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleShareSubmit}>
            Share
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default SharedFiles; 