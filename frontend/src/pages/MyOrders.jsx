import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './MyOrders.css';

const MyOrders = () => {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [filter, setFilter] = useState('');
  const [page, setPage] = useState(1);
  const [userRole, setUserRole] = useState('');

  const fetchOrders = useCallback(async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = { page, size: 20 };
      if (filter) {
        params.status = filter;
      }

      const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/orders/my`, {
        headers: { Authorization: `Bearer ${token}` },
        params
      });

      setOrders(response.data);
    } catch (err) {
      console.error('获取订单列表失败:', err);
    } finally {
      setIsLoading(false);
    }
  }, [page, filter]);

  useEffect(() => {
    setUserRole(localStorage.getItem('role') || 'user');
    fetchOrders();
  }, [fetchOrders]);

  const getStatusText = (status) => {
    const statusMap = {
      'pending': '待接单',
      'pending_review': '待审核',
      'accepted': '进行中',
      'completed': '已完成',
      'cancelled': '已取消'
    };
    return statusMap[status] || status;
  };

  const getStatusClass = (status) => {
    const classMap = {
      'pending': 'status-pending',
      'pending_review': 'status-pending-review',
      'accepted': 'status-accepted',
      'completed': 'status-completed',
      'cancelled': 'status-cancelled'
    };
    return classMap[status] || '';
  };

  const getItemSummary = (order) => {
    if (order.items && order.items.length > 0) {
      const summaries = order.items.slice(0, 2).map(item => 
        `${item.projectName} x${item.quantity}`
      );
      if (order.items.length > 2) {
        summaries.push('...');
      }
      return summaries.join(', ');
    }
    // 兼容历史订单
    if (order.projectName) {
      return `${order.projectName} x${order.quantity || 1}`;
    }
    if (order.customName) {
      return `自定义：${order.customName}`;
    }
    return '-';
  };

  const handleBack = () => {
    const role = localStorage.getItem('role') || 'user';
    navigate(`/${role}`);
  };

  const handleViewOrder = (orderId) => {
    const role = localStorage.getItem('role') || 'user';
    navigate(`/${role}/orders/${orderId}`);
  };

  const handleCancelOrder = async (orderId) => {
    if (!confirm('确定要取消这个订单吗？')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.post(`${import.meta.env.VITE_API_BASE_URL}/orders/${orderId}/cancel`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert('订单已取消');
      fetchOrders();
    } catch (err) {
      alert('取消订单失败：' + (err.response?.data?.detail || err.message));
      console.error('Cancel order error:', err);
    }
  };

  return (
    <div className="my-orders-container">
      <div className="my-orders-content">
        <header className="my-orders-header">
          <h1>我的订单</h1>
          <button onClick={handleBack} className="back-btn">返回</button>
        </header>

        <div className="filter-section">
          <div className="filter-group">
            <label>状态筛选：</label>
            <select
              value={filter}
              onChange={(e) => {
                setFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">全部状态</option>
              <option value="pending">待接单</option>
              <option value="accepted">进行中</option>
              <option value="completed">已完成</option>
              <option value="cancelled">已取消</option>
            </select>
          </div>
        </div>

        {isLoading && orders.length === 0 ? (
          <div className="loading-state">加载中...</div>
        ) : orders.length === 0 ? (
          <div className="empty-state">
            <p>暂无订单</p>
            <p>发布您的第一个订单吧</p>
          </div>
        ) : (
          <div className="orders-list">
            {orders.map(order => (
              <div key={order.id} className="order-card">
                <div className="order-header">
                  <div className="order-title">
                    <h3>订单号：{order.orderNo}</h3>
                    <span className={`status-badge ${getStatusClass(order.status)}`}>
                      {getStatusText(order.status)}
                    </span>
                  </div>
                  <div className="order-date">
                    {new Date(order.createdAt).toLocaleString('zh-CN')}
                  </div>
                </div>
                
                <div className="order-body">
                  <div className="order-info">
                    <span className="info-label">游戏：</span>
                    <span className="info-value">{order.gameName || '自定义游戏'}</span>
                  </div>
                  
                  <div className="order-info">
                    <span className="info-label">项目：</span>
                    <span className="info-value item-summary">{getItemSummary(order)}</span>
                  </div>
                  
                  <div className="order-info">
                    <span className="info-label">金额：</span>
                    <span className="info-value price">¥{order.totalAmount}</span>
                  </div>
                  
                  {order.requirements && (
                    <div className="order-info">
                      <span className="info-label">要求：</span>
                      <span className="info-value">{order.requirements}</span>
                    </div>
                  )}
                  
                  {order.handlerId && (
                    <div className="order-info">
                      <span className="info-label">打手ID：</span>
                      <span className="info-value">#{order.handlerId}</span>
                    </div>
                  )}
                </div>
                
                <div className="order-actions">
                  <button
                    onClick={() => handleViewOrder(order.id)}
                    className="view-btn"
                  >
                    查看详情
                  </button>
                  {userRole === 'user' && order.status === 'pending' && (
                    <button
                      onClick={() => handleCancelOrder(order.id)}
                      className="cancel-btn"
                    >
                      取消订单
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="pagination">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1 || isLoading}
            className="page-btn"
          >
            上一页
          </button>
          <span className="page-info">第 {page} 页</span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={orders.length < 20 || isLoading}
            className="page-btn"
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  );
};

export default MyOrders;
