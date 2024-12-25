import React, { useState, useEffect } from 'react';
import { Container, Form, Button, Alert, Image } from 'react-bootstrap';
import { setupMFA, verifyMFA } from '../../services/api';

const MFASetup = () => {
  const [qrCode, setQrCode] = useState('');
  const [secret, setSecret] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    const fetchMFASetup = async () => {
      try {
        const response = await setupMFA();
        setQrCode(response.qr_code);
        setSecret(response.secret);
      } catch (err) {
        setError('Failed to setup MFA. Please try again.');
      }
    };

    fetchMFASetup();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await verifyMFA(code);
      setSuccess('MFA setup completed successfully!');
      // Redirect to login after successful setup
      setTimeout(() => {
        window.location.href = '/login';
      }, 2000);
    } catch (err) {
      setError('Invalid code. Please try again.');
    }
  };

  return (
    <Container className="mt-5" style={{ maxWidth: '500px' }}>
      <h2 className="mb-4">Set Up Two-Factor Authentication</h2>
      
      {error && <Alert variant="danger">{error}</Alert>}
      {success && <Alert variant="success">{success}</Alert>}

      <div className="mb-4">
        <h4>Instructions:</h4>
        <ol>
          <li>Download Google Authenticator or any TOTP-based authenticator app</li>
          <li>Scan the QR code below with your authenticator app</li>
          <li>Enter the 6-digit code from your authenticator app to verify setup</li>
        </ol>
      </div>

      {qrCode && (
        <div className="text-center mb-4">
          <Image 
            src={`data:image/png;base64,${qrCode}`} 
            alt="QR Code"
            style={{ maxWidth: '200px' }}
          />
        </div>
      )}

      {secret && (
        <div className="mb-4">
          <p>If you can't scan the QR code, enter this secret key manually:</p>
          <code className="d-block p-2 bg-light">{secret}</code>
        </div>
      )}

      <Form onSubmit={handleSubmit}>
        <Form.Group className="mb-3">
          <Form.Label>Verification Code</Form.Label>
          <Form.Control
            type="text"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Enter 6-digit code"
            maxLength="6"
          />
        </Form.Group>

        <Button variant="primary" type="submit">
          Verify and Complete Setup
        </Button>
      </Form>
    </Container>
  );
};

export default MFASetup; 