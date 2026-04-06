import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Register from './components/Register';
import ProtectedRoute from './components/ProtectedRoute';
import UserDashboard from './pages/UserDashboard';
import HandlerDashboard from './pages/HandlerDashboard';
import AdminDashboard from './pages/AdminDashboard';
import AdminUsers from './pages/AdminUsers';
import AdminOrders from './pages/AdminOrders';
import AdminGames from './pages/AdminGames';
import CreateOrder from './pages/CreateOrder';
import OrderPool from './pages/OrderPool';
import MyOrders from './pages/MyOrders';
import OrderDetail from './pages/OrderDetail';
import MessageList from './pages/MessageList';
import Chat from './pages/Chat';
import AdminOrderReview from './pages/AdminOrderReview';

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('token'));
  const [userRole, setUserRole] = useState(localStorage.getItem('role'));

  useEffect(() => {
    const checkAuth = () => {
      setIsAuthenticated(!!localStorage.getItem('token'));
      setUserRole(localStorage.getItem('role'));
    };

    checkAuth();

    window.addEventListener('storage', checkAuth);
    window.addEventListener('auth-change', checkAuth);

    return () => {
      window.removeEventListener('storage', checkAuth);
      window.removeEventListener('auth-change', checkAuth);
    };
  }, []);

  return (
    <Router>
      <Routes>
        <Route 
          path="/" 
          element={isAuthenticated ? <Navigate to={`/${userRole}`} /> : <Login />} 
        />
        
        <Route 
          path="/register" 
          element={isAuthenticated ? <Navigate to={`/${userRole}`} /> : <Register />} 
        />
        
        <Route 
          path="/user" 
          element={
            <ProtectedRoute requiredRole="user">
              <UserDashboard />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/user/create-order" 
          element={
            <ProtectedRoute requiredRole="user">
              <CreateOrder />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/user/orders" 
          element={
            <ProtectedRoute requiredRole="user">
              <MyOrders />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/user/orders/:orderId" 
          element={
            <ProtectedRoute requiredRole="user">
              <OrderDetail />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/user/messages" 
          element={
            <ProtectedRoute requiredRole="user">
              <MessageList />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/user/messages/:conversationId" 
          element={
            <ProtectedRoute requiredRole="user">
              <Chat />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/handler" 
          element={
            <ProtectedRoute requiredRole="handler">
              <HandlerDashboard />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/handler/order-pool" 
          element={
            <ProtectedRoute requiredRole="handler">
              <OrderPool />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/handler/orders" 
          element={
            <ProtectedRoute requiredRole="handler">
              <MyOrders />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/handler/orders/:orderId" 
          element={
            <ProtectedRoute requiredRole="handler">
              <OrderDetail />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/handler/messages" 
          element={
            <ProtectedRoute requiredRole="handler">
              <MessageList />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/handler/messages/:conversationId" 
          element={
            <ProtectedRoute requiredRole="handler">
              <Chat />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/admin" 
          element={
            <ProtectedRoute requiredRole="admin">
              <AdminDashboard />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/admin/users" 
          element={
            <ProtectedRoute requiredRole="admin">
              <AdminUsers />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/admin/orders" 
          element={
            <ProtectedRoute requiredRole="admin">
              <AdminOrders />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/admin/orders/:orderId" 
          element={
            <ProtectedRoute requiredRole="admin">
              <OrderDetail />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/admin/games" 
          element={
            <ProtectedRoute requiredRole="admin">
              <AdminGames />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/admin/order-review" 
          element={
            <ProtectedRoute requiredRole="admin">
              <AdminOrderReview />
            </ProtectedRoute>
          } 
        />
        
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
};

export default App;
