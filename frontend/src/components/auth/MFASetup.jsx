import React, { useState, useEffect } from 'react';
import { Container, Form, Button, Alert, Image } from 'react-bootstrap';
import { setupMFA, verifyMFA } from '../../services/api';
import './Auth.css';

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
    <Container className="mfa-container mt-5">
      <div className="text-center mb-5">
        <h2 className="mfa-title">Enhance Your Security</h2>
        <p className="mfa-subtitle">Set up two-factor authentication to protect your account</p>
      </div>
      
      {error && <Alert variant="danger" className="fade show">{error}</Alert>}
      {success && <Alert variant="success" className="fade show">{success}</Alert>}

      <div className="d-flex gap-4 mb-4">
        <div className="mfa-card" style={{flex: 1}}>
          <h5 className="auth-title mb-3">Setup Instructions</h5>
          <ol className="list-group list-group-flush list-group-numbered text-start">
            <li className="list-group-item border-0">Download Google Authenticator or any TOTP-based authenticator app.</li>
            <li className="list-group-item border-0">Scan the QR code below with your authenticator app.</li>
            {secret && (
                <li className="list-group-item border-0">
                If you can't scan the QR code, enter this secret key manually: <br/>
                <code className="user-select-all fs-5 text-primary">{secret}</code>
                </li>
            )}
            <li className="list-group-item border-0">Enter the 6-digit code from your authenticator app to verify setup.</li>
          </ol>
        </div>

        {qrCode && (
          <div className="mfa-card text-center" style={{flex: 1}}>
            <div className="d-inline-block">
              <Image 
                src={`data:image/png;base64,${qrCode}`} 
                alt="QR Code"
                style={{ maxWidth: '300px' }}
                className="img-fluid"
              />
            </div>
          </div>
        )}
      </div>

      <Form onSubmit={handleSubmit} className="text-center">
        <Form.Group className="mb-3" style={{ maxWidth: '300px', margin: '0 auto' }}>
          <Form.Label className="auth-form-label fs-4">Verification Code</Form.Label>
          <Form.Control
            type="text"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder="Enter 6-digit code"
            maxLength="6"
          />
        </Form.Group>

        <Button variant="primary" type="submit" className="auth-button">
          Verify and Complete Setup
        </Button>
      </Form>
    </Container>
  );
};

export default MFASetup; 