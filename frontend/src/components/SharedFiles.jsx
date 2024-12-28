import React, { useState, useEffect } from 'react';
import { Container, Table, Button, Alert, Modal, Form } from 'react-bootstrap';
import { getSharedFiles, downloadFile, deleteFile, shareFile, createShareableLink } from '../services/api';
import './FileManager.css';
import { useSelector } from 'react-redux';

const SharedFiles = () => {
  const { user } = useSelector(state => state.auth);
  const [files, setFiles] = useState([]);
  const [error, setError] = useState('');
  const [showShareModal, setShowShareModal] = useState(false);
  const [selectedFileId, setSelectedFileId] = useState(null);
  const [userEmailToShare, setUserEmailToShare] = useState('');
  const [showLinkModal, setShowLinkModal] = useState(false);
  const [shareableLink, setShareableLink] = useState(null);
  const [linkDuration, setLinkDuration] = useState(1);

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

  const handleCreateLink = async () => {
    try {
      const response = await createShareableLink(selectedFileId, linkDuration);
      setShareableLink(response);
    } catch (error) {
      setError('Failed to create shareable link');
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

      <Modal show={showLinkModal} onHide={() => setShowLinkModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Create Shareable Link</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {error && <Alert variant="danger">{error}</Alert>}
          {shareableLink ? (
            <div>
              <p>Link created successfully! Expires in {linkDuration} hours.</p>
              <Form.Group>
                <Form.Control
                  type="text"
                  value={shareableLink.url}
                  readOnly
                  onClick={(e) => e.target.select()}
                />
              </Form.Group>
            </div>
          ) : (
            <Form>
              <Form.Group>
                <Form.Label>Link Duration (hours)</Form.Label>
                <Form.Control
                  type="number"
                  min="1"
                  max="24"
                  value={linkDuration}
                  onChange={(e) => setLinkDuration(parseInt(e.target.value))}
                />
                <Form.Text className="text-muted">
                  Choose between 1 and 24 hours
                </Form.Text>
              </Form.Group>
            </Form>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => {
            setShowLinkModal(false);
            setShareableLink(null);
            setLinkDuration(1);
          }}>
            Close
          </Button>
          {!shareableLink && (
            <Button variant="primary" onClick={handleCreateLink}>
              Create Link
            </Button>
          )}
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default SharedFiles; 