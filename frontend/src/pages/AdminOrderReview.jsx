import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './AdminOrderReview.css';

const AdminOrderReview = () => {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [error, setError] = useState('');

  const fetchPendingOrders = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/orders/pending-review`,
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { page, size: 20 }
        }
      );
      setOrders(response.data);
    } catch (err) {
      console.error('获取待审核订单失败:', err);
      setError('获取待审核订单失败');
    } finally {
      setIsLoading(false);
    }
  }, [page]);

  useEffect(() => {
    fetchPendingOrders();
  }, [fetchPendingOrders]);

  const handleApprove = async (orderId) => {
    if (!confirm('确定要批准这个订单吗？')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/orders/${orderId}/approve`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert('订单已批准');
      fetchPendingOrders();
    } catch (err) {
      alert('批准订单失败：' + (err.response?.data?.detail || err.message));
      console.error('Approve order error:', err);
    }
  };

  const handleReject = async (orderId) => {
    const remark = prompt('请输入拒绝原因（可选）：');
    if (remark === null) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/orders/${orderId}/reject`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
          params: { remark: remark || '' }
        }
      );
      alert('订单已拒绝');
      fetchPendingOrders();
    } catch (err) {
      alert('拒绝订单失败：' + (err.response?.data?.detail || err.message));
      console.error('Reject order error:', err);
    }
  };

  const handleViewOrder = (orderId) => {
    navigate(`/admin/orders/${orderId}`);
  };

  const handleBack = () => {
    navigate('/admin');
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
    return '-';
  };

  return (
    <div className="admin-order-review-container">
      <div className="admin-order-review-content">
        <header className="admin-order-review-header">
          <h1>订单审核</h1>
          <button onClick={handleBack} className="back-btn">返回</button>
        </header>

        {error && <div className="error-message">{error}</div>}

        {isLoading && orders.length === 0 ? (
          <div className="loading-state">加载中...</div>
        ) : orders.length === 0 ? (
          <div className="empty-state">
            <p>暂无待审核订单</p>
          </div>
        ) : (
          <div className="orders-list">
            {orders.map(order => (
              <div key={order.id} className="order-card">
                <div className="order-header">
                  <div className="order-title">
                    <h3>订单号：{order.orderNo}</h3>
                    <span className="status-badge status-pending-review">
                      待审核
                    </span>
                  </div>
                  <div className="order-date">
                    {new Date(order.createdAt).toLocaleString('zh-CN')}
                  </div>
                </div>
                
                <div className="order-body">
                  <div className="order-info">
                    <span className="info-label">发单人：</span>
                    <span className="info-value">{order.userName || `用户#${order.userId}`}</span>
                  </div>
                  
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
                </div>
                
                <div className="order-actions">
                  <button
                    onClick={() => handleViewOrder(order.id)}
                    className="view-btn"
                  >
                    查看详情
                  </button>
                  <button
                    onClick={() => handleApprove(order.id)}
                    className="approve-btn"
                  >
                    批准
                  </button>
                  <button
                    onClick={() => handleReject(order.id)}
                    className="reject-btn"
                  >
                    拒绝
                  </button>
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

export default AdminOrderReview;
