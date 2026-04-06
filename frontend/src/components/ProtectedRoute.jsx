import React from 'react';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children, requiredRole }) => {
  const isAuthenticated = !!localStorage.getItem('token');
  const userRole = localStorage.getItem('role');

  if (!isAuthenticated) {
    return <Navigate to="/" />;
  }
  if (requiredRole && userRole !== requiredRole) {
    return <Navigate to={`/${userRole}`} />;
  }
  return children;
};

export default ProtectedRoute;
