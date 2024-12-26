import React from 'react';
import { Container } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import NavigationBar from './Navbar';
import { logout as logoutAction } from '../../features/auth/authSlice';
import { logout as logoutAPI } from '../../services/api';

const Layout = ({ children }) => {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const handleLogout = async () => {
    try {
      await logoutAPI();
      dispatch(logoutAction());
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
      // Even if the API call fails, we should still clear the local state
      dispatch(logoutAction());
      navigate('/login');
    }
  };

  return (
    <div>
      <NavigationBar onLogout={handleLogout} />
      <Container className="mt-5">
        {children}
      </Container>
    </div>
  );
};

export default Layout; 