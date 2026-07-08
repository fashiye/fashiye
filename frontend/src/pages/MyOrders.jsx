import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import styles from './MyOrders.module.css';

const MyOrders = () => {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [filter, setFilter] = useState('');
  const [page, setPage] = useState(1);
  const [userRole, setUserRole] = useState('');

  const [异常弹窗, set异常弹窗] = useState(false);
  const [异常订单编号, set异常订单编号] = useState(null);
  const [异常原因, set异常原因] = useState('');

  const fetchOrders = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = { page, size: 20 };
      if (filter) {
        params.status = filter;
      }

      const response = await api.get('/orders/my', { params });

      // 传入：api返回的响应对象
      // 作用：从后端标准响应中提取data字段（订单列表数组）
      // 传出：订单列表数组
      const 订单列表 = response.data?.data ?? response.data ?? [];
      setOrders(Array.isArray(订单列表) ? 订单列表 : []);
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
    return statusMap[status] || status;
  };

  const getStatusClass = (status) => {
    const classMap = {
      'pending': 'status-pending',
      'pending_review': 'status-pending-review',
      'accepted': 'status-accepted',
      'in_progress': 'status-accepted',
      'completed': 'status-completed',
      'cancelled': 'status-cancelled',
      'abnormal': 'status-abnormal'
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
      await api.post(`/orders/${orderId}/cancel`);

      alert('订单已取消');
      fetchOrders();
    } catch (err) {
      alert('取消订单失败：' + (err.response?.data?.detail || err.message));
      console.error('Cancel order error:', err);
    }
  };

  const handleStartOrder = async (orderId) => {
    if (!confirm('确定要开始执行这个订单吗？')) {
      return;
    }

    try {
      await api.post(`/orders/${orderId}/status`, { action: 'start' });

      alert('已开始执行订单');
      fetchOrders();
    } catch (err) {
      alert('操作失败：' + (err.response?.data?.detail || err.message));
      console.error('Start order error:', err);
    }
  };

  const handleSubmitComplete = async (orderId) => {
    if (!confirm('确定要提交完成这个订单吗？')) {
      return;
    }

    try {
      await api.post(`/orders/${orderId}/status`, { action: 'submit_review' });

      alert('已提交完成，等待用户验收');
      fetchOrders();
    } catch (err) {
      alert('操作失败：' + (err.response?.data?.detail || err.message));
      console.error('Submit complete error:', err);
    }
  };

  const handleReportAbnormal = (orderId) => {
    set异常订单编号(orderId);
    set异常原因('');
    set异常弹窗(true);
  };

  const handleSubmitAbnormal = async () => {
    if (!异常原因.trim()) {
      alert('请输入异常原因');
      return;
    }

    try {
      await api.post(`/orders/${异常订单编号}/status`, {
        action: 'report_abnormal',
        remark: 异常原因.trim()
      });

      alert('已提交异常报告');
      set异常弹窗(false);
      set异常订单编号(null);
      set异常原因('');
      fetchOrders();
    } catch (err) {
      alert('操作失败：' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className={styles.myOrdersContainer}>
      <div className={styles.myOrdersContent}>
        <header className={styles.myOrdersHeader}>
          <h1>我的订单</h1>
          <button onClick={handleBack} className={styles.backBtn}>返回</button>
        </header>

        <div className={styles.filterSection}>
          <div className={styles.filterGroup}>
            <label>状态筛选：</label>
            <select
              value={filter}
              onChange={(e) => {
                setFilter(e.target.value);
                setPage(1);
              }}
            >
              <option value="">全部状态</option>
              <option value="pending">待支付</option>
              <option value="pending_review">待审核</option>
              <option value="accepted">已接单</option>
              <option value="in_progress">进行中</option>
              <option value="review">验收中</option>
              <option value="completed">已完成</option>
              <option value="cancelled">已取消</option>
              <option value="disputed">争议中</option>
              <option value="abnormal">异常</option>
            </select>
          </div>
        </div>

        {isLoading && orders.length === 0 ? (
          <div className={styles.loadingState}>加载中...</div>
        ) : orders.length === 0 ? (
          <div className={styles.emptyState}>
            <p>暂无订单</p>
            <p>发布您的第一个订单吧</p>
          </div>
        ) : (
          <div className={styles.ordersList}>
            {orders.map(order => (
              <div key={order.id} className={styles.orderCard}>
                <div className={styles.orderHeader}>
                  <div className={styles.orderTitle}>
                    <h3>订单号：{order.orderNo}</h3>
                    <span className={`${styles.statusBadge} ${styles[getStatusClass(order.status)]}`}>
                      {getStatusText(order.status)}
                    </span>
                  </div>
                  <div className={styles.orderDate}>
                    {new Date(order.createdAt).toLocaleString('zh-CN')}
                  </div>
                </div>
                
                <div className={styles.orderBody}>
                  <div className={styles.orderInfo}>
                    <span className={styles.infoLabel}>游戏：</span>
                    <span className={styles.infoValue}>{order.gameName || '自定义游戏'}</span>
                  </div>
                  
                  <div className={styles.orderInfo}>
                    <span className={styles.infoLabel}>项目：</span>
                    <span className={`${styles.infoValue} ${styles.itemSummary}`}>{getItemSummary(order)}</span>
                  </div>
                  
                  <div className={styles.orderInfo}>
                    <span className={styles.infoLabel}>金额：</span>
                    <span className={`${styles.infoValue} ${styles.price}`}>¥{order.totalAmount}</span>
                  </div>
                  
                  {order.requirements && (
                    <div className={styles.orderInfo}>
                      <span className={styles.infoLabel}>要求：</span>
                      <span className={styles.infoValue}>{order.requirements}</span>
                    </div>
                  )}
                  
                  {order.handlerId && (
                    <div className={styles.orderInfo}>
                      <span className={styles.infoLabel}>打手ID：</span>
                      <span className={styles.infoValue}>#{order.handlerId}</span>
                    </div>
                  )}
                </div>
                
                <div className={styles.orderActions}>
                  <button
                    onClick={() => handleViewOrder(order.id)}
                    className={styles.viewBtn}
                  >
                    查看详情
                  </button>
                  {userRole === 'user' && order.status === 'pending' && (
                    <button
                      onClick={() => handleCancelOrder(order.id)}
                      className={styles.cancelBtn}
                    >
                      取消订单
                    </button>
                  )}
                  {userRole === 'handler' && order.status === 'accepted' && (
                    <button
                      onClick={() => handleStartOrder(order.id)}
                      className={styles.acceptBtn}
                    >
                      开始执行
                    </button>
                  )}
                  {userRole === 'handler' && order.status === 'in_progress' && (
                    <button
                      onClick={() => handleSubmitComplete(order.id)}
                      className={styles.completeBtn}
                    >
                      提交完成
                    </button>
                  )}
                  {userRole === 'handler' && order.status === 'in_progress' && (
                    <button
                      onClick={() => handleReportAbnormal(order.id)}
                      className={styles.abnormalBtn}
                    >
                      提交异常
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className={styles.pagination}>
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1 || isLoading}
            className={styles.pageBtn}
          >
            上一页
          </button>
          <span className={styles.pageInfo}>第 {page} 页</span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={orders.length < 20 || isLoading}
            className={styles.pageBtn}
          >
            下一页
          </button>
        </div>
      </div>

      {异常弹窗 && (
        <div className={styles.modalOverlay} onClick={() => set异常弹窗(false)}>
          <div className={styles.abnormalModal} onClick={e => e.stopPropagation()}>
            <h3 className={styles.modalTitle}>提交异常报告</h3>
            <p className={styles.modalDesc}>请描述订单执行过程中遇到的问题：</p>
            <textarea
              className={styles.modalTextarea}
              value={异常原因}
              onChange={e => set异常原因(e.target.value)}
              placeholder="请输入异常原因..."
              rows={4}
            />
            <div className={styles.modalActions}>
              <button className={`${styles.modalBtn} ${styles.cancel}`} onClick={() => set异常弹窗(false)}>取消</button>
              <button className={`${styles.modalBtn} ${styles.confirm} ${styles.abnormal}`} onClick={handleSubmitAbnormal}>提交异常</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MyOrders;
