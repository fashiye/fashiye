import React from 'react';
import { useNavigate } from 'react-router-dom';
import './HandlerDashboard.css';

const HandlerDashboard = () => {
  const navigate = useNavigate();
  
  const handleLogout = () => {
    localStorage.clear();
    window.dispatchEvent(new Event('auth-change'));
    navigate('/');
  };

  const handleOrderPool = () => {
    navigate('/handler/order-pool');
  };

  const handleMyOrders = () => {
    navigate('/handler/orders');
  };

  const handleMessages = () => {
    navigate('/handler/messages');
  };

  return (
    <div className="dashboard-container handler-dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>打手中心</h1>
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
            <h3>订单池</h3>
            <p>查看可接的新订单</p>
            <button className="card-btn" onClick={handleOrderPool}>查看订单池</button>
          </div>
          
          <div className="dashboard-card">
            <h3>我的订单</h3>
            <p>管理我接的订单</p>
            <button className="card-btn" onClick={handleMyOrders}>查看订单</button>
          </div>
          
          <div className="dashboard-card">
            <h3>消息中心</h3>
            <p>与客户的聊天记录</p>
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

export default HandlerDashboard;