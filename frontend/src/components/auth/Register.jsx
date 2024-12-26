import React, { useState } from 'react';
import { Form, Button, Container, Alert } from 'react-bootstrap';
import { validateEmail, validatePassword } from '../../utils/validation';
import { register } from '../../services/api';
import { Link } from 'react-router-dom';
import './Auth.css';

const Register = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState({});
  const [success, setSuccess] = useState('');

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: '' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const newErrors = {};

    // Validate email
    if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Validate password
    const passwordValidation = validatePassword(formData.password);
    if (!passwordValidation.isValid) {
      newErrors.password = passwordValidation.message;
    }

    // Validate password confirmation
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      await register({
        email: formData.email,
        password: formData.password,
      });
      setSuccess('Registration successful! Please login to continue.');
      setFormData({ email: '', password: '', confirmPassword: '' });
    } catch (error) {
      if (error.response?.data?.email?.[0] === "user with this email already exists.") {
        setErrors({
          submit: 'An account with this email already exists. Please login instead.',
        });
      } else {
        setErrors({
          submit: error.response?.data?.message || 'Registration failed. Please try again.',
        });
      }
    }
  };

  return (
    <Container className="auth-container">
      <div className="auth-card">
        <h2 className="auth-title">Register</h2>
        {success && <Alert variant="success">{success}</Alert>}
        {errors.submit && <Alert variant="danger">{errors.submit}</Alert>}
        
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3">
            <Form.Label className="auth-form-label">Email address</Form.Label>
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
            <Form.Label className="auth-form-label">Password</Form.Label>
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

          <Form.Group className="mb-3">
            <Form.Label className="auth-form-label">Confirm Password</Form.Label>
            <Form.Control
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              isInvalid={!!errors.confirmPassword}
            />
            <Form.Control.Feedback type="invalid">
              {errors.confirmPassword}
            </Form.Control.Feedback>
          </Form.Group>

          <Button variant="primary" type="submit" className="auth-button me-2">
            Register
          </Button>
          
          <p className="mt-3">
            Already have an account? <Link to="/login" className="auth-link">Login here</Link>
          </p>
        </Form>
      </div>
    </Container>
  );
};

export default Register; 