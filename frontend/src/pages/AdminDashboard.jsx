import React from 'react';
import { useNavigate } from 'react-router-dom';
import './AdminDashboard.css';

const AdminDashboard = () => {
  const navigate = useNavigate();
  
  const handleLogout = () => {
    localStorage.clear();
    window.dispatchEvent(new Event('auth-change'));
    navigate('/');
  };

  const handleUserManagement = () => {
    navigate('/admin/users');
  };

  const handleOrderManagement = () => {
    navigate('/admin/orders');
  };

  const handleOrderReview = () => {
    navigate('/admin/order-review');
  };

  const handleGameManagement = () => {
    navigate('/admin/games');
  };

  const handleSystemSettings = () => {
    navigate('/admin/settings');
  };

  const handleDatabaseManagement = () => {
    navigate('/admin/database');
  };

  return (
    <div className="dashboard-container admin-dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>管理中心</h1>
        </div>
        <div className="header-right">
          <button className="logout-btn" onClick={handleLogout}>
            退出登录
          </button>
        </div>
      </header>
      
      <main className="dashboard-content">
        <div className="dashboard-grid">
          <div className="dashboard-card">
            <h3>用户管理</h3>
            <p>管理平台用户</p>
            <button className="card-btn" onClick={handleUserManagement}>用户列表</button>
          </div>
          
          <div className="dashboard-card">
            <h3>订单管理</h3>
            <p>管理所有订单</p>
            <button className="card-btn" onClick={handleOrderManagement}>订单列表</button>
          </div>
          
          <div className="dashboard-card">
            <h3>订单审核</h3>
            <p>审核待处理订单</p>
            <button className="card-btn" onClick={handleOrderReview}>审核订单</button>
          </div>
          
          <div className="dashboard-card">
            <h3>游戏管理</h3>
            <p>管理游戏和项目</p>
            <button className="card-btn" onClick={handleGameManagement}>游戏设置</button>
          </div>
          
          <div className="dashboard-card">
            <h3>系统设置</h3>
            <p>平台系统配置</p>
            <button className="card-btn" onClick={handleSystemSettings}>系统设置</button>
          </div>
          
          <div className="dashboard-card">
            <h3>数据库管理</h3>
            <p>直接管理数据库表数据</p>
            <button className="card-btn" onClick={handleDatabaseManagement}>数据库管理</button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdminDashboard;