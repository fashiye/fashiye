import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import './AdminDashboard.css';

const AdminOrders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState({ show: false, orderId: null, orderNo: '' });

  useEffect(() => {
    fetchOrders();
    fetchCurrentUser();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await api.get('/orders/all');
      setOrders(response.data);
    } catch (err) {
      console.error('获取订单列表失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get('/auth/me');
      setCurrentUser(response.data);
    } catch (err) {
      console.error('获取当前用户失败:', err);
    }
  };

  const getStatusText = (status) => {
    const statusMap = {
      'pending': '待接单',
      'accepted': '已接单',
      'in_progress': '进行中',
      'review': '待验收',
      'completed': '已完成',
      'cancelled': '已取消',
      'pending_review': '待审核'
    };
    return statusMap[status] || status;
  };

  const handleDeleteClick = (orderId, orderNo) => {
    setDeleteConfirm({ show: true, orderId, orderNo });
  };

  const handleDeleteConfirm = async () => {
    try {
      await api.delete(`/orders/${deleteConfirm.orderId}`);
      setOrders(orders.filter(order => order.id !== deleteConfirm.orderId));
      setDeleteConfirm({ show: false, orderId: null, orderNo: '' });
      alert('订单删除成功！');
    } catch (err) {
      console.error('删除订单失败:', err);
      alert(err.response?.data?.message || '删除订单失败');
    }
  };

  const handleDeleteCancel = () => {
    setDeleteConfirm({ show: false, orderId: null, orderNo: '' });
  };

  const handleForceComplete = async (orderId, orderNo) => {
    if (!confirm(`确定要强制完成订单 ${orderNo} 吗？`)) return;
    try {
      await api.post(`/orders/${orderId}/status`, { action: 'confirm_complete' });
      alert('订单已强制完成！');
      fetchOrders();
    } catch (err) {
      alert('操作失败：' + (err.response?.data?.detail || err.message));
    }
  };

  const isSuperAdmin = currentUser?.role === 'super';

  return (
    <div className="dashboard-container admin-dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>订单管理</h1>
        </div>
        <div className="header-right">
          <button className="logout-btn" onClick={() => window.history.back()}>
            返回
          </button>
        </div>
      </header>
      
      <main className="dashboard-content">
        {loading ? (
          <div className="loading">加载中...</div>
        ) : (
          <div className="orders-list">
            <table className="data-table">
              <thead>
                <tr>
                  <th>订单号</th>
                  <th>用户</th>
                  <th>打手</th>
                  <th>金额</th>
                  <th>状态</th>
                  <th>创建时间</th>
                  {isSuperAdmin && <th>操作</th>}
                </tr>
              </thead>
              <tbody>
                {orders.map(order => (
                  <tr key={order.id}>
                    <td>{order.orderNo || '-'}</td>
                    <td>{order.userName || order.userId || '-'}</td>
                    <td>{order.handlerName || order.handlerId || '-'}</td>
                    <td>¥{order.totalAmount || 0}</td>
                    <td>{getStatusText(order.status)}</td>
                    <td>{order.createdAt ? new Date(order.createdAt).toLocaleString() : '-'}</td>
                    {isSuperAdmin && (
                      <td>
                        <button
                          onClick={() => handleDeleteClick(order.id, order.orderNo)}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: '#dc3545',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            marginRight: '6px'
                          }}
                        >
                          删除
                        </button>
                        {(order.status === 'review' || order.status === 'in_progress') && (
                          <button
                            onClick={() => handleForceComplete(order.id, order.orderNo)}
                            style={{
                              padding: '6px 12px',
                              backgroundColor: '#16a34a',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer'
                            }}
                          >
                            强制完成
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {deleteConfirm.show && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}>
            <div style={{
              backgroundColor: 'white',
              padding: '20px',
              borderRadius: '8px',
              maxWidth: '400px',
              width: '90%'
            }}>
              <h3 style={{ marginTop: 0 }}>确认删除</h3>
              <p>确定要删除订单 <strong>{deleteConfirm.orderNo}</strong> 吗？</p>
              <p style={{ color: '#666', fontSize: '14px' }}>此操作不可恢复</p>
              <div style={{ marginTop: '20px', textAlign: 'right' }}>
                <button
                  onClick={handleDeleteCancel}
                  style={{
                    padding: '8px 16px',
                    marginRight: '10px',
                    border: '1px solid #ddd',
                    backgroundColor: 'white',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  取消
                </button>
                <button
                  onClick={handleDeleteConfirm}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#dc3545',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  确认删除
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default AdminOrders;
