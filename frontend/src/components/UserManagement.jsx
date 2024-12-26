import React, { useState, useEffect } from 'react';
import { Table, Button, Form, Modal } from 'react-bootstrap';
import { getUsers, updateUserRole } from '../services/api';

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedRole, setSelectedRole] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const data = await getUsers();
      setUsers(data);
    } catch (error) {
      setError('Failed to fetch users');
    }
  };

  const handleEdit = (user) => {
    setSelectedUser(user);
    setSelectedRole(user.role);
    setShowEditModal(true);
  };

  const handleSave = async () => {
    try {
      await updateUserRole(selectedUser.id, selectedRole);
      setShowEditModal(false);
      fetchUsers(); // Refresh the user list
    } catch (error) {
      setError('Failed to update user role');
    }
  };

  return (
    <div className="container mt-4">
      <h2>User Management</h2>
      {error && <div className="alert alert-danger">{error}</div>}
      
      <Table striped bordered hover>
        <thead>
          <tr>
            <th>Email</th>
            <th>Role</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map(user => (
            <tr key={user.id}>
              <td>{user.email}</td>
              <td>{user.role}</td>
              <td>
                <Button 
                  variant="primary" 
                  size="sm"
                  onClick={() => handleEdit(user)}
                >
                  Edit
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      <Modal show={showEditModal} onHide={() => setShowEditModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Edit User Role</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form>
            <Form.Group>
              <Form.Label>Email</Form.Label>
              <Form.Control 
                type="text" 
                value={selectedUser?.email || ''} 
                disabled 
              />
            </Form.Group>
            <Form.Group className="mt-3">
              <Form.Label>Role</Form.Label>
              <Form.Select
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value)}
              >
                <option value="ADMIN">Admin</option>
                <option value="USER">Regular User</option>
                <option value="GUEST">Guest</option>
              </Form.Select>
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowEditModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSave}>
            Save Changes
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default UserManagement; 