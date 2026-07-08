import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../utils/api';
import ChatPanel from '../components/ChatPanel';
import styles from './OrderDetail.module.css';

const OrderDetail = () => {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const 当前用户 = JSON.parse(localStorage.getItem('user') || '{}');
  const 当前角色 = localStorage.getItem('role');

  const 是发单人 = (order) => 当前用户?.id === order?.userId && 当前角色 === 'user';
  const 是接单人 = (order) => 当前用户?.id === order?.handlerId && 当前角色 === 'handler';

  useEffect(() => {
    fetchOrderDetail();
  }, [orderId]);

  const fetchOrderDetail = async () => {
    setIsLoading(true);
    try {
      const response = await api.get(`/orders/${orderId}`);
      setOrder(response.data.data);
    } catch (err) {
      console.error('获取订单详情失败:', err);
      setError(err.response?.data?.detail || '获取订单详情失败');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusText = (status) => {
    const map = {
      'pending': '待支付',
      'pending_review': '待审核',
      'accepted': '已接单',
      'in_progress': '进行中',
      'review': '验收中',
      'completed': '已完成',
      'cancelled': '已取消',
      'disputed': '争议中',
      'abnormal': '异常'
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
      'disputed': 'status-disputed',
      'abnormal': 'status-abnormal'
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
      await api.post(`/orders/${orderId}/cancel`);
      alert('订单已取消');
      fetchOrderDetail();
    } catch (err) {
      alert('取消订单失败：' + (err.response?.data?.detail || err.message));
    }
  };

  const handleStartOrder = async () => {
    if (!confirm('确定开始执行订单？')) return;
    try {
      await api.post(`/orders/${orderId}/status`, { action: 'start' });
      alert('已标记为开始执行');
      fetchOrderDetail();
    } catch (err) {
      alert('操作失败：' + (err.response?.data?.detail || err.message));
    }
  };

  const handleSubmitComplete = async () => {
    if (!confirm('确定提交完成？提交后将等待发单人验收。')) return;
    try {
      await api.post(`/orders/${orderId}/status`, { action: 'submit_complete' });
      alert('已提交完成，等待发单人验收');
      fetchOrderDetail();
    } catch (err) {
      alert('操作失败：' + (err.response?.data?.detail || err.message));
    }
  };

  const handleConfirmComplete = async () => {
    if (!confirm('确认订单已完成？确认后订单将标记为已完成状态。')) return;
    try {
      await api.post(`/orders/${orderId}/status`, { action: 'confirm_complete' });
      alert('订单已完成！');
      fetchOrderDetail();
    } catch (err) {
      alert('操作失败：' + (err.response?.data?.detail || err.message));
    }
  };

  if (isLoading) {
    return (
      <div className={styles.orderDetailContainer}>
        <div className={styles.orderDetailContent}>
          <div className={styles.loadingState}>加载中...</div>
        </div>
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className={styles.orderDetailContainer}>
        <div className={styles.orderDetailContent}>
          <div className={styles.errorState}>
            <p>{error || '订单不存在'}</p>
            <button onClick={handleBack} className={styles.backBtn}>返回</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.orderDetailContainer}>
      <div className={styles.orderDetailContent}>
        <header className={styles.orderDetailHeader}>
          <div className={styles.headerLeft}>
            <button onClick={handleBack} className={styles.backBtn}>← 返回</button>
            <h1>订单详情</h1>
          </div>
          <span className={`${styles.statusBadge} ${getStatusClass(order.status)}`}>
            {getStatusText(order.status)}
          </span>
        </header>

        <div className={styles.detailGrid}>
          <div className={styles.detailSection}>
            <h2 className={styles.sectionTitle}>订单信息</h2>
            <div className={styles.infoGrid}>
              <div className={styles.infoItem}>
                <span className={styles.infoLabel}>订单号</span>
                <span className={`${styles.infoValue} ${styles.orderNo}`}>{order.orderNo}</span>
              </div>
              <div className={styles.infoItem}>
                <span className={styles.infoLabel}>游戏</span>
                <span className={styles.infoValue}>{order.gameName || '-'}</span>
              </div>
              <div className={styles.infoItem}>
                <span className={styles.infoLabel}>总金额</span>
                <span className={`${styles.infoValue} ${styles.price}`}>¥{order.totalAmount}</span>
              </div>
            </div>
          </div>

          {/* 项目列表 */}
          <div className={styles.detailSection}>
            <h2 className={styles.sectionTitle}>项目明细</h2>
            <div className={styles.itemsTable}>
              <div className={styles.itemsHeader}>
                <span className={styles.itemName}>项目名称</span>
                <span className={styles.itemQty}>数量</span>
                <span className={styles.itemPrice}>单价</span>
                <span className={styles.itemTotal}>小计</span>
              </div>
              {order.items && order.items.length > 0 ? (
                order.items.map((item, index) => (
                  <div key={index} className={styles.itemRow}>
                    <span className={styles.itemName}>{item.projectName}</span>
                    <span className={styles.itemQty}>{item.quantity}</span>
                    <span className={styles.itemPrice}>¥{item.unitPrice}</span>
                    <span className={styles.itemTotal}>¥{item.totalPrice}</span>
                  </div>
                ))
              ) : (
                <div className={styles.itemRow}>
                  <span className={styles.itemName}>{order.projectName || '-'}</span>
                  <span className={styles.itemQty}>{order.quantity || 1}</span>
                  <span className={styles.itemPrice}>¥{order.unitPrice || order.totalAmount}</span>
                  <span className={styles.itemTotal}>¥{order.totalAmount}</span>
                </div>
              )}
            </div>
          </div>

          <div className={styles.detailSection}>
            <h2 className={styles.sectionTitle}>人员信息</h2>
            <div className={styles.infoGrid}>
              <div className={styles.infoItem}>
                <span className={styles.infoLabel}>发单人</span>
                <span className={styles.infoValue}>{order.userName || `用户#${order.userId}`}</span>
              </div>
              <div className={styles.infoItem}>
                <span className={styles.infoLabel}>接单人</span>
                <span className={styles.infoValue}>
                  {order.handlerName ? order.handlerName : (order.handlerId ? `打手#${order.handlerId}` : '暂无')}
                </span>
              </div>
            </div>
          </div>

          <div className={styles.detailSection}>
            <h2 className={styles.sectionTitle}>账号与备注</h2>
            <div className={styles.infoList}>
              <div className={styles.infoItemFull}>
                <span className={styles.infoLabel}>账号密码</span>
                <span className={`${styles.infoValue} ${styles.accountInfo}`}>{order.accountInfo || '未提供'}</span>
              </div>
              <div className={styles.infoItemFull}>
                <span className={styles.infoLabel}>需求备注</span>
                <span className={styles.infoValue}>{order.requirements || '无'}</span>
              </div>
            </div>
          </div>

          <div className={styles.detailSection}>
            <h2 className={styles.sectionTitle}>时间记录</h2>
            <div className={styles.infoGrid}>
              <div className={styles.infoItem}>
                <span className={styles.infoLabel}>发单时间</span>
                <span className={styles.infoValue}>{formatTime(order.createdAt)}</span>
              </div>
              <div className={styles.infoItem}>
                <span className={styles.infoLabel}>接单时间</span>
                <span className={styles.infoValue}>{formatTime(order.acceptedAt)}</span>
              </div>
              <div className={styles.infoItem}>
                <span className={styles.infoLabel}>完成时间</span>
                <span className={styles.infoValue}>{formatTime(order.completedAt)}</span>
              </div>
              <div className={styles.infoItem}>
                <span className={styles.infoLabel}>取消时间</span>
                <span className={styles.infoValue}>{formatTime(order.cancelledAt)}</span>
              </div>
              <div className={styles.infoItem}>
                <span className={styles.infoLabel}>最后更新</span>
                <span className={styles.infoValue}>{formatTime(order.updatedAt)}</span>
              </div>
            </div>
          </div>

          {order.abnormalReason && (
            <div className={styles.detailSection}>
              <h2 className={styles.sectionTitle}>异常信息</h2>
              <div className={styles.infoList}>
                <div className={styles.infoItemFull}>
                  <span className={styles.infoLabel}>异常原因</span>
                  <span className={styles.infoValue} style={{ color: '#d97706' }}>{order.abnormalReason}</span>
                </div>
              </div>
            </div>
          )}

          {(order.userComment || order.handlerComment) && (
            <div className={styles.detailSection}>
              <h2 className={styles.sectionTitle}>评价信息</h2>
              <div className={styles.infoList}>
                {order.userComment && (
                  <div className={styles.infoItemFull}>
                    <span className={styles.infoLabel}>发单人评价</span>
                    <span className={styles.infoValue}>
                      {'⭐'.repeat(order.userRating || 0)} {order.userComment}
                    </span>
                  </div>
                )}
                {order.handlerComment && (
                  <div className={styles.infoItemFull}>
                    <span className={styles.infoLabel}>接单人评价</span>
                    <span className={styles.infoValue}>
                      {'⭐'.repeat(order.handlerRating || 0)} {order.handlerComment}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className={`${styles.detailSection} ${styles.chatSection}`}>
            <ChatPanel 
              orderId={parseInt(orderId)} 
              handlerId={order.handlerId} 
              userId={order.userId} 
            />
          </div>
        </div>

        <div className={styles.detailActions}>
          {是发单人(order) && (order.status === 'pending' || order.status === 'pending_review') && (
            <button onClick={() => navigate(`/payment/${orderId}`)} className={styles.payBtn}>去支付</button>
          )}
          {是发单人(order) && order.status === 'pending' && (
            <button onClick={handleCancelOrder} className={styles.cancelBtn}>取消订单</button>
          )}
          {是发单人(order) && order.status === 'review' && (
            <button onClick={handleConfirmComplete} className={styles.confirmBtn}>确认完成</button>
          )}
          {是接单人(order) && order.status === 'accepted' && (
            <button onClick={handleStartOrder} className={styles.confirmBtn}>开始执行</button>
          )}
          {是接单人(order) && order.status === 'in_progress' && (
            <button onClick={handleSubmitComplete} className={styles.confirmBtn}>提交完成</button>
          )}
        </div>
      </div>
    </div>
  );
};

export default OrderDetail;
