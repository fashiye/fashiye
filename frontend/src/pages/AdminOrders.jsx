import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import 样式 from './AdminDashboard.module.css';

const AdminOrders = () => {
  const [订单列表, set订单列表] = useState([]);
  const [加载中, set加载中] = useState(true);
  const [当前页, set当前页] = useState(1);
  const [总页数, set总页数] = useState(1);
  const [总条数, set总条数] = useState(0);
  const [当前用户, set当前用户] = useState(null);
  const [选中ID集合, set选中ID集合] = useState(new Set());
  const [删除确认弹窗, set删除确认弹窗] = useState({ show: false, ids: [], 类型: 'single' });
  const [提示, set提示] = useState({ show: false, type: 'success', message: '' });
  const 每页条数 = 10;

  useEffect(() => {
    fetchOrders();
    fetchCurrentUser();
  }, [当前页]);

  useEffect(() => {
    if (提示.show) {
      const 定时器 = setTimeout(() => set提示({ show: false, type: '', message: '' }), 3000);
      return () => clearTimeout(定时器);
    }
  }, [提示.show]);

  const 显示提示 = (message, type = 'success') => {
    set提示({ show: true, type, message });
  };

  const fetchOrders = async () => {
    set加载中(true);
    try {
      const 响应 = await api.get('/orders/all', { params: { page: 当前页, size: 每页条数 } });
      set订单列表(响应.data.data || []);
      set总条数(响应.data.total || 0);
      set总页数(Math.ceil((响应.data.total || 0) / 每页条数));
    } catch (错误) {
      console.error('获取订单列表失败:', 错误);
      显示提示('获取订单列表失败', 'error');
    } finally {
      set加载中(false);
    }
  };

  const fetchCurrentUser = async () => {
    try {
      const 响应 = await api.get('/users/me');
      set当前用户(响应.data.data);
    } catch (错误) {
      console.error('获取当前用户失败:', 错误);
    }
  };

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

  // 全选/取消全选
  const 切换全选 = () => {
    if (选中ID集合.size === 订单列表.length) {
      set选中ID集合(new Set());
    } else {
      set选中ID集合(new Set(订单列表.map(o => o.id)));
    }
  };

  // 切换单个选中
  const 切换选中 = (id) => {
    const 新集合 = new Set(选中ID集合);
    if (新集合.has(id)) {
      新集合.delete(id);
    } else {
      新集合.add(id);
    }
    set选中ID集合(新集合);
  };

  // 点击单个删除
  const 处理删除点击 = (id, orderNo) => {
    set删除确认弹窗({ show: true, ids: [id], orderNo, 类型: 'single' });
  };

  // 点击批量删除
  const 处理批量删除点击 = () => {
    if (选中ID集合.size === 0) return;
    set删除确认弹窗({ show: true, ids: [...选中ID集合], orderNo: `${选中ID集合.size}个订单`, 类型: 'batch' });
  };

  // 确认删除
  const 处理删除确认 = async () => {
    const { ids } = 删除确认弹窗;
    try {
      await Promise.all(ids.map(id => api.delete(`/orders/${id}`)));
      set订单列表(prev => prev.filter(order => !ids.includes(order.id)));
      set选中ID集合(new Set());
      set删除确认弹窗({ show: false, ids: [], orderNo: '', 类型: 'single' });
      显示提示(`成功删除 ${ids.length} 个订单`);
    } catch (错误) {
      console.error('删除订单失败:', 错误);
      显示提示(错误.response?.data?.message || '删除订单失败', 'error');
    }
  };

  const 处理删除取消 = () => {
    set删除确认弹窗({ show: false, ids: [], orderNo: '', 类型: 'single' });
  };

  const 处理强制完成 = async (id, orderNo) => {
    if (!window.confirm(`确定要强制完成订单 ${orderNo} 吗？`)) return;
    try {
      await api.post(`/orders/${id}/status`, { action: 'confirm_complete' });
      显示提示('订单已强制完成');
      fetchOrders();
    } catch (错误) {
      显示提示('操作失败：' + (错误.response?.data?.detail || 错误.message), 'error');
    }
  };

  const isSuperAdmin = 当前用户?.role === 'super';

  const 渲染分页 = () => {
    if (总页数 <= 1) return null;
    const 页码 = [];
    for (let i = 1; i <= 总页数; i++) {
      页码.push(
        <button
          key={i}
          onClick={() => set当前页(i)}
          style={{
            padding: '8px 12px', margin: '0 4px', border: '1px solid #ddd',
            backgroundColor: i === 当前页 ? '#007bff' : 'white',
            color: i === 当前页 ? 'white' : '#333', cursor: 'pointer', borderRadius: '4px'
          }}
        >
          {i}
        </button>
      );
    }
    return 页码;
  };

  return (
    <div className={样式.dashboardContainer}>
      {/* 气泡提示 */}
      {提示.show && (
        <div style={{
          position: 'fixed', top: '20px', right: '20px', zIndex: 9999,
          padding: '12px 24px', borderRadius: '6px',
          backgroundColor: 提示.type === 'success' ? '#d4edda' : '#f8d7da',
          color: 提示.type === 'success' ? '#155724' : '#721c24',
          border: `1px solid ${提示.type === 'success' ? '#c3e6cb' : '#f5c6cb'}`,
          boxShadow: '0 2px 12px rgba(0,0,0,0.15)',
          fontSize: '14px', fontWeight: 500,
          transition: 'opacity 0.3s ease'
        }}>
          {提示.message}
        </div>
      )}

      <header className={样式.dashboardHeader}>
        <div className={样式.headerLeft}>
          <h1>订单管理</h1>
        </div>
        <div className={样式.headerRight}>
          <button className={样式.logoutBtn} onClick={() => window.history.back()}>返回</button>
        </div>
      </header>

      <main className={样式.dashboardContent}>
        <div style={{ marginBottom: '15px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ color: '#666', fontSize: '14px' }}>
            共 {总条数} 条记录
            {选中ID集合.size > 0 && (
              <span style={{ marginLeft: '10px', color: '#007bff' }}>
                （已选 {选中ID集合.size} 项）
              </span>
            )}
          </div>
          {isSuperAdmin && 选中ID集合.size > 0 && (
            <button
              onClick={处理批量删除点击}
              style={{
                padding: '6px 16px', backgroundColor: '#dc3545', color: 'white',
                border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px'
              }}
            >
              批量删除（{选中ID集合.size}）
            </button>
          )}
        </div>

        {加载中 ? (
          <div className={样式.loading}>加载中...</div>
        ) : (
          <div className={样式.ordersList}>
            <table className={样式.dataTable}>
              <thead>
                <tr>
                  {isSuperAdmin && (
                    <th style={{ width: '40px' }}>
                      <input
                        type="checkbox"
                        checked={订单列表.length > 0 && 选中ID集合.size === 订单列表.length}
                        onChange={切换全选}
                        style={{ cursor: 'pointer' }}
                      />
                    </th>
                  )}
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
                {订单列表.map(order => (
                  <tr key={order.id} style={{
                    backgroundColor: 选中ID集合.has(order.id) ? '#f0f7ff' : 'transparent'
                  }}>
                    {isSuperAdmin && (
                      <td>
                        <input
                          type="checkbox"
                          checked={选中ID集合.has(order.id)}
                          onChange={() => 切换选中(order.id)}
                          style={{ cursor: 'pointer' }}
                        />
                      </td>
                    )}
                    <td>{order.orderNo || '-'}</td>
                    <td>{order.userName || order.userId || '-'}</td>
                    <td>{order.handlerName || order.handlerId || '-'}</td>
                    <td>¥{order.totalAmount || 0}</td>
                    <td>{getStatusText(order.status)}</td>
                    <td>{order.createdAt ? new Date(order.createdAt).toLocaleString() : '-'}</td>
                    {isSuperAdmin && (
                      <td>
                        <button
                          onClick={() => 处理删除点击(order.id, order.orderNo)}
                          style={{
                            padding: '6px 12px',
                            backgroundColor: '#dc3545',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            marginRight: '6px',
                            fontSize: '13px'
                          }}
                        >
                          删除
                        </button>
                        {(order.status === 'review' || order.status === 'in_progress') && (
                          <button
                            onClick={() => 处理强制完成(order.id, order.orderNo)}
                            style={{
                              padding: '6px 12px',
                              backgroundColor: '#16a34a',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '13px'
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

            {/* 分页 */}
            {总页数 > 1 && (
              <div style={{
                display: 'flex', justifyContent: 'center', alignItems: 'center',
                marginTop: '20px', padding: '20px'
              }}>
                <button
                  onClick={() => set当前页(p => Math.max(1, p - 1))}
                  disabled={当前页 === 1}
                  style={{
                    padding: '8px 16px', margin: '0 4px', border: '1px solid #ddd',
                    backgroundColor: 当前页 === 1 ? '#f5f5f5' : 'white',
                    color: 当前页 === 1 ? '#ccc' : '#333',
                    cursor: 当前页 === 1 ? 'not-allowed' : 'pointer', borderRadius: '4px'
                  }}
                >
                  上一页
                </button>
                {渲染分页()}
                <button
                  onClick={() => set当前页(p => Math.min(总页数, p + 1))}
                  disabled={当前页 === 总页数}
                  style={{
                    padding: '8px 16px', margin: '0 4px', border: '1px solid #ddd',
                    backgroundColor: 当前页 === 总页数 ? '#f5f5f5' : 'white',
                    color: 当前页 === 总页数 ? '#ccc' : '#333',
                    cursor: 当前页 === 总页数 ? 'not-allowed' : 'pointer', borderRadius: '4px'
                  }}
                >
                  下一页
                </button>
                <span style={{ marginLeft: '20px', color: '#666', fontSize: '14px' }}>
                  共 {总条数} 条记录，第 {当前页}/{总页数} 页
                </span>
              </div>
            )}
          </div>
        )}

        {/* 删除确认弹窗 */}
        {删除确认弹窗.show && (
          <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex',
            alignItems: 'center', justifyContent: 'center', zIndex: 1000
          }}>
            <div style={{
              backgroundColor: 'white', padding: '24px', borderRadius: '8px',
              maxWidth: '400px', width: '90%', boxShadow: '0 4px 16px rgba(0,0,0,0.2)'
            }}>
              <h3 style={{ margin: '0 0 12px 0', fontSize: '16px' }}>确认删除</h3>
              <p style={{ margin: '0 0 4px 0', fontSize: '14px' }}>
                确定要删除 <strong>{删除确认弹窗.orderNo}</strong>
                {删除确认弹窗.类型 === 'batch' ? ' 吗？' : ' 吗？'}
              </p>
              <p style={{ color: '#999', fontSize: '13px', margin: '8px 0 0 0' }}>
                此操作不可恢复
              </p>
              <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  onClick={处理删除取消}
                  style={{
                    padding: '8px 20px', backgroundColor: '#6c757d', color: 'white',
                    border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '14px'
                  }}
                >
                  取消
                </button>
                <button
                  onClick={处理删除确认}
                  style={{
                    padding: '8px 20px', backgroundColor: '#dc3545', color: 'white',
                    border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '14px'
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
