import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import 样式 from './AdminOrderReview.module.css';

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
      const response = await api.get('/orders/pending-review', {
        params: { page, size: 20 }
      });
      setOrders(response.data.data);
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
      await api.post(`/orders/${orderId}/approve`);
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
      await api.post(`/orders/${orderId}/reject`, {}, {
        params: { remark: remark || '' }
      });
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
    <div className={样式.adminOrderReviewContainer}>
      <div className={样式.adminOrderReviewContent}>
        <header className={样式.adminOrderReviewHeader}>
          <h1>订单审核</h1>
          <button onClick={handleBack} className={样式.backBtn}>返回</button>
        </header>

        {error && <div className={样式.errorMessage}>{error}</div>}
        {isLoading ? (
          <div className={样式.loadingState}>加载中...</div>
        ) : orders.length === 0 ? (
          <div className={样式.emptyState}>
            <p>暂无待审核订单</p>
          </div>
        ) : (
          <div className={样式.ordersList}>
            {orders.map(order => (
              <div key={order.id} className={样式.orderCard}>
                <div className={样式.orderHeader}>
                  <div className={样式.orderTitle}>
                    <h3>订单号：{order.orderNo}</h3>
                    <span className={`${样式.statusBadge} ${样式.statusPendingReview}`}>
                      待审核
                    </span>
                  </div>
                  <div className={样式.orderDate}>
                    {new Date(order.createdAt).toLocaleString('zh-CN')}
                  </div>
                </div>
                
                <div className={样式.orderBody}>
                  <div className={样式.orderInfo}>
                    <span className={样式.infoLabel}>发单人：</span>
                    <span className={样式.infoValue}>{order.userName || `用户#${order.userId}`}</span>
                  </div>
                  <div className={样式.orderInfo}>
                    <span className={样式.infoLabel}>游戏：</span>
                    <span className={样式.infoValue}>{order.gameName || '自定义游戏'}</span>
                  </div>
                  <div className={样式.orderInfo}>
                    <span className={样式.infoLabel}>项目：</span>
                    <span className={样式.infoValue}>{getItemSummary(order)}</span>
                  </div>
                  <div className={样式.orderInfo}>
                    <span className={样式.infoLabel}>金额：</span>
                    <span className={`${样式.infoValue} ${样式.price}`}>¥{order.totalAmount}</span>
                  </div>
                  
                  {order.requirements && (
                    <div className={样式.orderInfo}>
                      <span className={样式.infoLabel}>要求：</span>
                      <span className={样式.infoValue}>{order.requirements}</span>
                    </div>
                  )}
                </div>
                
                <div className={样式.orderActions}>
                  <button
                    onClick={() => handleViewOrder(order.id)}
                    className={样式.viewBtn}
                  >
                    查看详情
                  </button>
                  <button
                    onClick={() => handleApprove(order.id)}
                    className={样式.approveBtn}
                  >
                    批准
                  </button>
                  <button
                    onClick={() => handleReject(order.id)}
                    className={样式.rejectBtn}
                  >
                    拒绝
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className={样式.pagination}>
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1 || isLoading}
            className={样式.pageBtn}
          >
            上一页
          </button>
          <span className={样式.pageInfo}>第 {page} 页</span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={orders.length < 20 || isLoading}
            className={样式.pageBtn}
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminOrderReview;
