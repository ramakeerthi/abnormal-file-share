import React from 'react';
import { Container } from 'react-bootstrap';

const Home = () => {
  return (
    <Container className="text-center">
      <h1>Welcome to File Share Application</h1>
      <p className="mt-4">
        A secure platform for sharing files with end-to-end encryption and two-factor authentication.
      </p>
    </Container>
  );
};

export default Home; 