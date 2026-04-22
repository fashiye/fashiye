import React from 'react';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children, requiredRole }) => {
  const isAuthenticated = !!localStorage.getItem('token');
  const userRole = localStorage.getItem('role');

  if (!isAuthenticated) {
    return <Navigate to="/" />;
  }
  
  // 定义角色层级：super > operator > admin > handler > user
  const roleHierarchy = {
    'super': 5,
    'operator': 4,
    'admin': 3,
    'handler': 2,
    'user': 1
  };
  
  // 如果指定了requiredRole，检查用户角色权限
  if (requiredRole) {
    const userLevel = roleHierarchy[userRole] || 0;
    const requiredLevel = roleHierarchy[requiredRole] || 0;
    
    // 用户角色权限不足，重定向到对应的首页
    if (userLevel < requiredLevel) {
      // super和operator角色重定向到admin页面
      const redirectPath = userRole === 'super' || userRole === 'operator' ? 'admin' : userRole;
      return <Navigate to={`/${redirectPath}`} />;
    }
  }
  
  return children;
};

export default ProtectedRoute;
