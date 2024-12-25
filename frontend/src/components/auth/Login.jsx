import React, { useState } from 'react';
import { Form, Button, Container, Alert } from 'react-bootstrap';
import { validateEmail } from '../../utils/validation';
import { login, loginWithMFA } from '../../services/api';
import { Link } from 'react-router-dom';

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    totpCode: '',
  });
  const [errors, setErrors] = useState({});
  const [mfaRequired, setMfaRequired] = useState(false);
  const [mfaSetupRequired, setMfaSetupRequired] = useState(false);
  const [tempTokens, setTempTokens] = useState(null);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: '' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const newErrors = {};

    if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      if (mfaRequired) {
        const response = await loginWithMFA({
          email: formData.email,
          password: formData.password,
          totp_code: formData.totpCode,
        });
        // Handle successful login with MFA
        localStorage.setItem('access_token', response.access);
        localStorage.setItem('refresh_token', response.refresh);
        localStorage.setItem('username', formData.email);
        localStorage.setItem('user_role', response.user_role);
        window.location.href = '/';
      } else {
        const response = await login({
          email: formData.email,
          password: formData.password,
        });

        if (response.mfa_required) {
          setMfaRequired(true);
          setTempTokens({
            temp_access_token: response.temp_access_token,
            temp_refresh_token: response.temp_refresh_token,
          });
          localStorage.setItem('user_role', response.user_role);
        } else if (response.mfa_setup_required) {
          setMfaSetupRequired(true);
          localStorage.setItem('access_token', response.temp_access_token);
          localStorage.setItem('refresh_token', response.temp_refresh_token);
          localStorage.setItem('username', formData.email);
          localStorage.setItem('user_role', response.user_role);
          window.location.href = '/mfa-setup';
        } else {
          // Normal login success
          localStorage.setItem('access_token', response.access);
          localStorage.setItem('refresh_token', response.refresh);
          localStorage.setItem('username', formData.email);
          localStorage.setItem('user_role', response.user_role);
          window.location.href = '/';
        }
      }
    } catch (error) {
      setErrors({
        submit: error.response?.data?.error || 'Login failed. Please try again.',
      });
    }
  };

  return (
    <Container className="mt-5" style={{ maxWidth: '500px' }}>
      <h2 className="mb-4">Login</h2>
      {errors.submit && <Alert variant="danger">{errors.submit}</Alert>}
      
      <Form onSubmit={handleSubmit}>
        <Form.Group className="mb-3">
          <Form.Label>Email address</Form.Label>
          <Form.Control
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            isInvalid={!!errors.email}
          />
          <Form.Control.Feedback type="invalid">
            {errors.email}
          </Form.Control.Feedback>
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Label>Password</Form.Label>
          <Form.Control
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            isInvalid={!!errors.password}
          />
          <Form.Control.Feedback type="invalid">
            {errors.password}
          </Form.Control.Feedback>
        </Form.Group>

        {mfaRequired && (
          <Form.Group className="mb-3">
            <Form.Label>Authentication Code</Form.Label>
            <Form.Control
              type="text"
              name="totpCode"
              value={formData.totpCode}
              onChange={handleChange}
              isInvalid={!!errors.totpCode}
              placeholder="Enter 6-digit code"
            />
            <Form.Control.Feedback type="invalid">
              {errors.totpCode}
            </Form.Control.Feedback>
          </Form.Group>
        )}

        <Button variant="primary" type="submit" className="me-2">
          {mfaRequired ? 'Verify' : 'Login'}
        </Button>
        
        <p className="mt-3">
          Don't have an account? <Link to="/register">Register here</Link>
        </p>
      </Form>
    </Container>
  );
};

export default Login; 