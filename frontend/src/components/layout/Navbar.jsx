import React from 'react';
import { Navbar, Container, Nav } from 'react-bootstrap';
import { Link, useLocation } from 'react-router-dom';
import { useSelector } from 'react-redux';
import './Navbar.css';

const NavigationBar = ({ onLogout }) => {
  const location = useLocation();
  const { user, isAuthenticated } = useSelector(state => state.auth);

  return (
    <Navbar bg="black" variant="dark" expand="lg" className="custom-navbar">
      <Container fluid className="px-3">
        <Navbar.Brand as={Link} to="/" className="me-0 nav-brand">
          <img src="/FileShare_logo.png" alt="FileShare Logo" height="60" />
        </Navbar.Brand>
        
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="me-auto">
            {isAuthenticated && user?.role === 'ADMIN' && (
              <Nav.Link as={Link} to="/users" className="ms-3">
                User Management
              </Nav.Link>
            )}
            <Nav.Link as={Link} to="/files" className="ms-3">
              File Manager
            </Nav.Link>
          </Nav>
          
          <Nav>
            {!isAuthenticated ? (
              (location.pathname !== '/login' && location.pathname !== '/register') && (
                <Nav.Link as={Link} to="/login">Login</Nav.Link>
              )
            ) : (
              <>
                <Navbar.Text className="me-3">
                  Welcome, {user?.email} ({user?.role})
                </Navbar.Text>
                <Nav.Link onClick={onLogout}>
                  Logout
                </Nav.Link>
              </>
            )}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default NavigationBar; 