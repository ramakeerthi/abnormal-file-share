import React from 'react';
import { Navbar, Container, Nav, Button } from 'react-bootstrap';
import { Link, useLocation } from 'react-router-dom';

const NavigationBar = ({ isLoggedIn, onLogout }) => {
  const location = useLocation();
  const username = localStorage.getItem('username') || 'User';
  const userRole = localStorage.getItem('user_role');

  return (
    <Navbar bg="black" variant="dark" expand="lg">
      <Container>
        <Navbar.Brand as={Link} to="/"><img src="/FileShare_logo.png" alt="FileShare Logo" height="60em" /></Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav" className="justify-content-end">
          <Nav>
            {!isLoggedIn ? (
              <>
                {location.pathname !== '/login' && (
                  <Nav.Link as={Link} to="/login">Login</Nav.Link>
                )}
              </>
            ) : (
              <>
                <Navbar.Text className="me-3">
                  Welcome, {username} ({userRole})
                </Navbar.Text>
                <Button variant="outline-light" onClick={onLogout}>
                  Logout
                </Button>
              </>
            )}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
};

export default NavigationBar; 