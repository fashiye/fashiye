import React from 'react';
import { useNavigate } from 'react-router-dom';
import './UserDashboard.css';

const UserDashboard = () => {
  const navigate = useNavigate();
  
  const handleLogout = () => {
    localStorage.clear();
    window.dispatchEvent(new Event('auth-change'));
    navigate('/');
  };

  const handleCreateOrder = () => {
    navigate('/user/create-order');
  };

  const handleMyOrders = () => {
    navigate('/user/orders');
  };

  const handleMessages = () => {
    navigate('/user/messages');
  };

  return (
    <div className="dashboard-container user-dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>玩家中心</h1>
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
            <h3>发布订单</h3>
            <p>发布新的游戏代练订单</p>
            <button className="card-btn" onClick={handleCreateOrder}>立即发布</button>
          </div>
          
          <div className="dashboard-card">
            <h3>我的订单</h3>
            <p>查看和管理我的订单</p>
            <button className="card-btn" onClick={handleMyOrders}>查看订单</button>
          </div>
          
          <div className="dashboard-card">
            <h3>消息中心</h3>
            <p>与打手的聊天记录</p>
            <button className="card-btn" onClick={handleMessages}>查看消息</button>
          </div>
          
          <div className="dashboard-card">
            <h3>账户管理</h3>
            <p>修改个人信息和密码</p>
            <button className="card-btn">账户设置</button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default UserDashboard;