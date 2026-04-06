import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './OrderDetail.css';

const OrderDetail = () => {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchOrderDetail();
  }, [orderId]);

  const fetchOrderDetail = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/orders/${orderId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setOrder(response.data);
    } catch (err) {
      console.error('获取订单详情失败:', err);
      setError(err.response?.data?.detail || '获取订单详情失败');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusText = (status) => {
    const map = {
      'pending': '待接单',
      'pending_review': '待审核',
      'accepted': '已接单',
      'in_progress': '进行中',
      'review': '待验收',
      'completed': '已完成',
      'cancelled': '已取消',
      'disputed': '争议中'
    };
    return map[status] || status;
  };

  const getStatusClass = (status) => {
    const map = {
      'pending': 'status-pending',
      'pending_review': 'status-pending-review',
      'accepted': 'status-accepted',
      'in_progress': 'status-in-progress',
      'review': 'status-review',
      'completed': 'status-completed',
      'cancelled': 'status-cancelled',
      'disputed': 'status-disputed'
    };
    return map[status] || '';
  };

  const formatTime = (time) => {
    if (!time) return '-';
    return new Date(time).toLocaleString('zh-CN');
  };

  const handleBack = () => {
    navigate(-1);
  };

  const handleCancelOrder = async () => {
    if (!confirm('确定要取消这个订单吗？')) return;
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/orders/${orderId}/cancel`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      alert('订单已取消');
      fetchOrderDetail();
    } catch (err) {
      alert('取消订单失败：' + (err.response?.data?.detail || err.message));
    }
  };

  if (isLoading) {
    return (
      <div className="order-detail-container">
        <div className="order-detail-content">
          <div className="loading-state">加载中...</div>
        </div>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="order-detail-container">
        <div className="order-detail-content">
          <div className="error-state">
            <p>{error || '订单不存在'}</p>
            <button onClick={handleBack} className="back-btn">返回</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="order-detail-container">
      <div className="order-detail-content">
        <header className="order-detail-header">
          <div className="header-left">
            <button onClick={handleBack} className="back-btn">← 返回</button>
            <h1>订单详情</h1>
          </div>
          <span className={`status-badge ${getStatusClass(order.status)}`}>
            {getStatusText(order.status)}
          </span>
        </header>

        <div className="detail-grid">
          <div className="detail-section">
            <h2 className="section-title">订单信息</h2>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">订单号</span>
                <span className="info-value order-no">{order.orderNo}</span>
              </div>
              <div className="info-item">
                <span className="info-label">游戏</span>
                <span className="info-value">{order.gameName || '-'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">总金额</span>
                <span className="info-value price">¥{order.totalAmount}</span>
              </div>
            </div>
          </div>

          {/* 项目列表 */}
          <div className="detail-section">
            <h2 className="section-title">项目明细</h2>
            <div className="items-table">
              <div className="items-header">
                <span className="item-name">项目名称</span>
                <span className="item-qty">数量</span>
                <span className="item-price">单价</span>
                <span className="item-total">小计</span>
              </div>
              {order.items && order.items.length > 0 ? (
                order.items.map((item, index) => (
                  <div key={index} className="item-row">
                    <span className="item-name">{item.projectName}</span>
                    <span className="item-qty">{item.quantity}</span>
                    <span className="item-price">¥{item.unitPrice}</span>
                    <span className="item-total">¥{item.totalPrice}</span>
                  </div>
                ))
              ) : (
                <div className="item-row">
                  <span className="item-name">{order.projectName || '-'}</span>
                  <span className="item-qty">{order.quantity || 1}</span>
                  <span className="item-price">¥{order.unitPrice || order.totalAmount}</span>
                  <span className="item-total">¥{order.totalAmount}</span>
                </div>
              )}
            </div>
          </div>

          <div className="detail-section">
            <h2 className="section-title">人员信息</h2>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">发单人</span>
                <span className="info-value">{order.userName || `用户#${order.userId}`}</span>
              </div>
              <div className="info-item">
                <span className="info-label">接单人</span>
                <span className="info-value">
                  {order.handlerName ? order.handlerName : (order.handlerId ? `打手#${order.handlerId}` : '暂无')}
                </span>
              </div>
            </div>
          </div>

          <div className="detail-section">
            <h2 className="section-title">账号与备注</h2>
            <div className="info-list">
              <div className="info-item-full">
                <span className="info-label">账号密码</span>
                <span className="info-value account-info">{order.accountInfo || '未提供'}</span>
              </div>
              <div className="info-item-full">
                <span className="info-label">需求备注</span>
                <span className="info-value">{order.requirements || '无'}</span>
              </div>
            </div>
          </div>

          <div className="detail-section">
            <h2 className="section-title">时间记录</h2>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">发单时间</span>
                <span className="info-value">{formatTime(order.createdAt)}</span>
              </div>
              <div className="info-item">
                <span className="info-label">接单时间</span>
                <span className="info-value">{formatTime(order.acceptedAt)}</span>
              </div>
              <div className="info-item">
                <span className="info-label">完成时间</span>
                <span className="info-value">{formatTime(order.completedAt)}</span>
              </div>
              <div className="info-item">
                <span className="info-label">取消时间</span>
                <span className="info-value">{formatTime(order.cancelledAt)}</span>
              </div>
              <div className="info-item">
                <span className="info-label">最后更新</span>
                <span className="info-value">{formatTime(order.updatedAt)}</span>
              </div>
            </div>
          </div>

          {(order.userComment || order.handlerComment) && (
            <div className="detail-section">
              <h2 className="section-title">评价信息</h2>
              <div className="info-list">
                {order.userComment && (
                  <div className="info-item-full">
                    <span className="info-label">发单人评价</span>
                    <span className="info-value">
                      {'⭐'.repeat(order.userRating || 0)} {order.userComment}
                    </span>
                  </div>
                )}
                {order.handlerComment && (
                  <div className="info-item-full">
                    <span className="info-label">接单人评价</span>
                    <span className="info-value">
                      {'⭐'.repeat(order.handlerRating || 0)} {order.handlerComment}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="detail-actions">
          {order.status === 'pending' && (
            <button onClick={handleCancelOrder} className="cancel-btn">取消订单</button>
          )}
        </div>
      </div>
    </div>
  );
};

export default OrderDetail;
