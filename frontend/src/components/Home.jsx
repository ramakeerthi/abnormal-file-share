import React from 'react';
import { Container, Card, Row, Col } from 'react-bootstrap';
import { FaLock, FaShareAlt, FaShieldAlt } from 'react-icons/fa';
import './Home.css';

const Home = () => {
  return (
    <Container className="mt-4">
      <div className="text-center mb-5">
        <h1 className="display-4 fw-bold text-black">Welcome to FileShare</h1>
        <p className="lead text-black">
          A secure platform for sharing files with end-to-end encryption and two-factor authentication.
        </p>
      </div>

      <Row className="g-4">
        <Col md={4}>
          <Card className="feature-card h-100">
            <Card.Body>
              <div className="icon-wrapper">
                <FaLock />
              </div>
              <Card.Title>Getting Started</Card.Title>
              <div className="feature-list">
                <div className="feature-item">Set up Two-Factor Authentication (2FA)</div>
                <div className="feature-item">Navigate to File Manager</div>
                <div className="feature-item">Access Shared Files section</div>
                <div className="feature-item">Automatic file encryption</div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col md={4}>
          <Card className="feature-card h-100">
            <Card.Body>
              <div className="icon-wrapper">
                <FaShareAlt />
              </div>
              <Card.Title>Sharing Features</Card.Title>
              <div className="feature-list">
                <div className="feature-item">
                  <span className="highlight">Share Files:</span> Share with other users via email
                </div>
                <div className="feature-item">
                  <span className="highlight">Permission Levels:</span>
                  <div className="sub-feature">• View Only access</div>
                  <div className="sub-feature">• View and Download access</div>
                </div>
                <div className="feature-item">
                  <span className="highlight">Management:</span> Upload, download, and share securely
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col md={4}>
          <Card className="feature-card h-100">
            <Card.Body>
              <div className="icon-wrapper">
                <FaShieldAlt />
              </div>
              <Card.Title>Security Practices</Card.Title>
              <div className="feature-list">
                <div className="feature-item">Secure 2FA device & backup codes</div>
                <div className="feature-item">Regular access review</div>
                <div className="feature-item">Strong password usage</div>
                <div className="feature-item">Verify recipient emails</div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Home; 