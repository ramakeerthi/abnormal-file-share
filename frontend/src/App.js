import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';
import Layout from './components/layout/Layout';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import MFASetup from './components/auth/MFASetup';
import Home from './components/Home';
import { useDispatch, useSelector } from 'react-redux';
import { loginSuccess, logout } from './features/auth/authSlice';
import { checkAuth } from './services/api';
import UserManagement from './components/UserManagement';

// Protected Route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useSelector(state => state.auth);
  return isAuthenticated ? children : <Navigate to="/login" />;
};

function App() {
  const dispatch = useDispatch();
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const verifyAuth = async () => {
      try {
        const data = await checkAuth();
        if (data.user) {
          dispatch(loginSuccess(data.user));
        }
      } catch (error) {
        console.log('Not authenticated');
      } finally {
        setIsLoading(false);
      }
    };

    verifyAuth();
    // eslint-disable-next-line
  }, []); // Only run once on mount

  useEffect(() => {
    let inactivityTimer;
    
    const resetTimer = () => {
      clearTimeout(inactivityTimer);
      inactivityTimer = setTimeout(() => {
        dispatch(logout());
        navigate('/login');
      }, 30 * 60 * 1000); // 30 minutes
    };

    window.addEventListener('mousemove', resetTimer);
    window.addEventListener('keypress', resetTimer);

    return () => {
      clearTimeout(inactivityTimer);
      window.removeEventListener('mousemove', resetTimer);
      window.removeEventListener('keypress', resetTimer);
    };
  }, [dispatch, navigate]);

  if (isLoading) {
    return <div>Loading...</div>; // Or your loading component
  }

  return (
    <Router>
      <div className="App">
        <Layout>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route 
              path="/mfa-setup" 
              element={
                <ProtectedRoute>
                  <MFASetup />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/" 
              element={
                <ProtectedRoute>
                  <Home />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/users" 
              element={
                <ProtectedRoute>
                  <UserManagement />
                </ProtectedRoute>
              } 
            />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </Layout>
      </div>
    </Router>
  );
}

export default App;
