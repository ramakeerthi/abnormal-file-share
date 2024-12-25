import React from 'react';
import { Container } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import NavigationBar from './Navbar';
import { logout } from '../../services/api';

const Layout = ({ children }) => {
  const isAuthenticated = localStorage.getItem('access_token');
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      const refresh_token = localStorage.getItem('refresh_token');
      await logout(refresh_token);
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('username');
      localStorage.removeItem('user_role');
      navigate('/login');
      window.location.reload();
    }
  };

  return (
    <div>
      <NavigationBar 
        isLoggedIn={!!isAuthenticated}
        onLogout={handleLogout}
      />
      <Container className="mt-5">
        {children}
      </Container>
    </div>
  );
};

export default Layout; 