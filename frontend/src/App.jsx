import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Register from './components/Register';
import ForgotPassword from './components/ForgotPassword';
import ResetPassword from './components/ResetPassword';
import ProtectedRoute from './components/ProtectedRoute';
import UserDashboard from './pages/UserDashboard';
import HandlerDashboard from './pages/HandlerDashboard';
import AdminDashboard from './pages/AdminDashboard';
import AdminUsers from './pages/AdminUsers';
import AdminHandlers from './pages/AdminHandlers';
import AdminAdmins from './pages/AdminAdmins';
import AdminOrders from './pages/AdminOrders';
import AdminGames from './pages/AdminGames';
import AdminGameProjects from './pages/AdminGameProjects';
import CreateOrder from './pages/CreateOrder';
import OrderPool from './pages/OrderPool';
import MyOrders from './pages/MyOrders';
import OrderDetail from './pages/OrderDetail';
import MessageList from './pages/MessageList';
import Chat from './pages/Chat';
import AdminOrderReview from './pages/AdminOrderReview';
import DatabaseAdmin from './pages/DatabaseAdmin';
import AccountSettings from './pages/AccountSettings';
import GameOrderPage from './pages/GameOrderPage';
import OrderLookup from './pages/OrderLookup';
import PaymentPage from './pages/PaymentPage';

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
          element={isAuthenticated ? <Navigate to={`/${userRole === 'super' || userRole === 'operator' ? 'admin' : userRole}`} /> : <Login />} 
        />
        
        <Route 
          path="/register" 
          element={isAuthenticated ? <Navigate to={`/${userRole}`} /> : <Register />} 
        />
        
        <Route 
          path="/forgot-password" 
          element={isAuthenticated ? <Navigate to={`/${userRole}`} /> : <ForgotPassword />} 
        />
        
        <Route 
          path="/reset-password" 
          element={isAuthenticated ? <Navigate to={`/${userRole}`} /> : <ResetPassword />} 
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
          path="/payment/:orderId" 
          element={<PaymentPage />}
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
          path="/user/account" 
          element={
            <ProtectedRoute requiredRole="user">
              <AccountSettings />
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
          path="/handler/account" 
          element={
            <ProtectedRoute requiredRole="handler">
              <AccountSettings />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/admin" 
          element={
            <ProtectedRoute requiredRole="operator">
              <AdminDashboard />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/admin/users" 
          element={
            <ProtectedRoute requiredRole="super">
              <AdminUsers />
            </ProtectedRoute>
          } 
        />

        <Route 
          path="/admin/handlers" 
          element={
            <ProtectedRoute requiredRole="super">
              <AdminHandlers />
            </ProtectedRoute>
          } 
        />

        <Route 
          path="/admin/admins" 
          element={
            <ProtectedRoute requiredRole="super">
              <AdminAdmins />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/admin/orders" 
          element={
            <ProtectedRoute requiredRole="operator">
              <AdminOrders />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/admin/orders/:orderId" 
          element={
            <ProtectedRoute requiredRole="operator">
              <OrderDetail />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/admin/games" 
          element={
            <ProtectedRoute requiredRole="operator">
              <AdminGames />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/admin/games/:gameId" 
          element={
            <ProtectedRoute requiredRole="operator">
              <AdminGameProjects />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/admin/order-review" 
          element={
            <ProtectedRoute requiredRole="operator">
              <AdminOrderReview />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/admin/database" 
          element={
            <ProtectedRoute requiredRole="super">
              <DatabaseAdmin />
            </ProtectedRoute>
          } 
        />
        
        {/* 公开页面 - 无需登录 */}
        <Route 
          path="/game-order" 
          element={<GameOrderPage />} 
        />
        
        <Route 
          path="/order-lookup" 
          element={<OrderLookup />} 
        />
        
        <Route 
          path="/order-detail/:orderId" 
          element={<OrderDetail />} 
        />
        
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  );
};

export default App;
