import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import 样式 from './AdminDashboard.module.css';

const AdminUsers = () => {
  const [用户列表, set用户列表] = useState([]);
  const [加载中, set加载中] = useState(true);
  const [当前页, set当前页] = useState(1);
  const [总页数, set总页数] = useState(1);
  const [总条数, set总条数] = useState(0);
  const [选中ID集合, set选中ID集合] = useState(new Set());
  const [删除确认弹窗, set删除确认弹窗] = useState({ show: false, ids: [], 提示文本: '' });
  const [封禁确认弹窗, set封禁确认弹窗] = useState({ show: false, ids: [], 提示文本: '', 目标状态: 1 });
  const [提示, set提示] = useState({ show: false, type: 'success', message: '' });
  const 每页条数 = 10;

  useEffect(() => {
    获取用户列表();
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

  const 获取用户列表 = async () => {
    set加载中(true);
    try {
      const 响应 = await api.get('/admin/users', { params: { page: 当前页, size: 每页条数 } });
      set用户列表(响应.data.data.items);
      set总页数(Math.ceil(响应.data.data.total / 每页条数));
      set总条数(响应.data.data.total);
    } catch (错误) {
      console.error('获取用户列表失败:', 错误);
      显示提示('获取用户列表失败', 'error');
    } finally {
      set加载中(false);
    }
  };

  // 全选/取消全选
  const 切换全选 = () => {
    if (选中ID集合.size === 用户列表.length) {
      set选中ID集合(new Set());
    } else {
      set选中ID集合(new Set(用户列表.map(u => u.id)));
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

  // 单个封禁/解禁
  const 处理封禁解禁 = async (用户id, 用户名, 当前状态) => {
    const 操作文本 = 当前状态 === 0 ? '封禁' : '解禁';
    set封禁确认弹窗({
      show: true,
      ids: [用户id],
      提示文本: `确定${操作文本}用户 "${用户名}" 吗？${操作文本 === '封禁' ? '被封禁用户无法登录系统。' : ''}`,
      目标状态: 当前状态 === 0 ? 1 : 0
    });
  };

  // 批量封禁/解禁
  const 处理批量封禁 = () => {
    if (选中ID集合.size === 0) return;
    const 选中用户 = 用户列表.filter(u => 选中ID集合.has(u.id));
    const 全部正常 = 选中用户.every(u => u.status === 0);
    const 操作文本 = 全部正常 ? '封禁' : '解禁';
    set封禁确认弹窗({
      show: true,
      ids: [...选中ID集合],
      提示文本: `确定${操作文本}选中的 ${选中ID集合.size} 个用户吗？`,
      目标状态: 全部正常 ? 1 : 0
    });
  };

  // 确认封禁/解禁
  const 封禁确认执行 = async () => {
    const { ids, 目标状态 } = 封禁确认弹窗;
    try {
      await Promise.all(ids.map(id => api.put(`/admin/users/${id}/status`, { status: 目标状态 })));
      set选中ID集合(new Set());
      set封禁确认弹窗({ show: false, ids: [], 提示文本: '', 目标状态: 1 });
      显示提示(`操作成功，已处理 ${ids.length} 个用户`);
      获取用户列表();
    } catch (错误) {
      显示提示(`操作失败: ${错误.response?.data?.detail || '未知错误'}`, 'error');
    }
  };

  // 单个删除
  const 处理删除用户 = (用户id, 用户名) => {
    set删除确认弹窗({
      show: true,
      ids: [用户id],
      提示文本: `确定要删除用户 "${用户名}" 吗？此操作不可恢复！`
    });
  };

  // 批量删除
  const 处理批量删除 = () => {
    if (选中ID集合.size === 0) return;
    set删除确认弹窗({
      show: true,
      ids: [...选中ID集合],
      提示文本: `确定要删除选中的 ${选中ID集合.size} 个用户吗？此操作不可恢复！`
    });
  };

  // 确认删除
  const 删除确认执行 = async () => {
    const { ids } = 删除确认弹窗;
    try {
      await Promise.all(ids.map(id => api.delete(`/admin/users/${id}`)));
      set选中ID集合(new Set());
      set删除确认弹窗({ show: false, ids: [], 提示文本: '' });
      显示提示(`成功删除 ${ids.length} 个用户`);
      获取用户列表();
    } catch (错误) {
      显示提示(`删除失败: ${错误.response?.data?.detail || '未知错误'}`, 'error');
    }
  };

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
          fontSize: '14px', fontWeight: 500
        }}>
          {提示.message}
        </div>
      )}

      <header className={样式.dashboardHeader}>
        <div className={样式.headerLeft}>
          <h1>用户管理</h1>
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
          {选中ID集合.size > 0 && (
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={处理批量封禁}
                style={{
                  padding: '6px 16px', backgroundColor: '#ffc107', color: '#333',
                  border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px'
                }}
              >
                批量封禁/解禁（{选中ID集合.size}）
              </button>
              <button
                onClick={处理批量删除}
                style={{
                  padding: '6px 16px', backgroundColor: '#dc3545', color: 'white',
                  border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px'
                }}
              >
                批量删除（{选中ID集合.size}）
              </button>
            </div>
          )}
        </div>

        {加载中 ? (
          <div className={样式.loading}>加载中...</div>
        ) : (
          <div className={样式.usersList}>
            <table className={样式.dataTable}>
              <thead>
                <tr>
                  <th style={{ width: '40px' }}>
                    <input
                      type="checkbox"
                      checked={用户列表.length > 0 && 选中ID集合.size === 用户列表.length}
                      onChange={切换全选}
                      style={{ cursor: 'pointer' }}
                    />
                  </th>
                  <th>ID</th>
                  <th>用户名</th>
                  <th>邮箱</th>
                  <th>状态</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {用户列表.map(用户 => (
                  <tr key={用户.id} style={{
                    backgroundColor: 选中ID集合.has(用户.id) ? '#f0f7ff' : 'transparent'
                  }}>
                    <td>
                      <input
                        type="checkbox"
                        checked={选中ID集合.has(用户.id)}
                        onChange={() => 切换选中(用户.id)}
                        style={{ cursor: 'pointer' }}
                      />
                    </td>
                    <td>{用户.id}</td>
                    <td>{用户.username}</td>
                    <td>{用户.email}</td>
                    <td>
                      <span style={{
                        padding: '3px 8px', borderRadius: '3px', fontSize: '13px',
                        backgroundColor: 用户.status === 0 ? '#d4edda' : '#f8d7da',
                        color: 用户.status === 0 ? '#155724' : '#721c24'
                      }}>
                        {用户.status === 0 ? '正常' : '已封禁'}
                      </span>
                    </td>
                    <td>{new Date(用户.createdAt).toLocaleString()}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '5px' }}>
                        <button
                          onClick={() => 处理封禁解禁(用户.id, 用户.username, 用户.status)}
                          style={{
                            padding: '5px 12px',
                            backgroundColor: 用户.status === 0 ? '#ffc107' : '#17a2b8',
                            color: 用户.status === 0 ? '#333' : 'white',
                            border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px'
                          }}
                        >
                          {用户.status === 0 ? '封禁' : '解禁'}
                        </button>
                        <button
                          onClick={() => 处理删除用户(用户.id, 用户.username)}
                          style={{
                            padding: '5px 12px', backgroundColor: '#dc3545', color: 'white',
                            border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px'
                          }}
                        >
                          删除
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {总页数 > 1 && (
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginTop: '20px', padding: '20px' }}>
                <button onClick={() => set当前页(p => Math.max(1, p - 1))} disabled={当前页 === 1} style={{
                  padding: '8px 16px', margin: '0 4px', border: '1px solid #ddd',
                  backgroundColor: 当前页 === 1 ? '#f5f5f5' : 'white',
                  color: 当前页 === 1 ? '#ccc' : '#333',
                  cursor: 当前页 === 1 ? 'not-allowed' : 'pointer', borderRadius: '4px'
                }}>上一页</button>
                {渲染分页()}
                <button onClick={() => set当前页(p => Math.min(总页数, p + 1))} disabled={当前页 === 总页数} style={{
                  padding: '8px 16px', margin: '0 4px', border: '1px solid #ddd',
                  backgroundColor: 当前页 === 总页数 ? '#f5f5f5' : 'white',
                  color: 当前页 === 总页数 ? '#ccc' : '#333',
                  cursor: 当前页 === 总页数 ? 'not-allowed' : 'pointer', borderRadius: '4px'
                }}>下一页</button>
                <span style={{ marginLeft: '20px', color: '#666' }}>
                  共 {总条数} 条记录，第 {当前页}/{总页数} 页
                </span>
              </div>
            )}
          </div>
        )}
      </main>

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
            <p style={{ fontSize: '14px' }}>{删除确认弹窗.提示文本}</p>
            <p style={{ color: '#999', fontSize: '13px', margin: '8px 0 0 0' }}>此操作不可恢复</p>
            <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button onClick={() => set删除确认弹窗({ show: false, ids: [], 提示文本: '' })}
                style={{ padding: '8px 20px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                取消
              </button>
              <button onClick={删除确认执行}
                style={{ padding: '8px 20px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                确认删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 封禁/解禁确认弹窗 */}
      {封禁确认弹窗.show && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex',
          alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white', padding: '24px', borderRadius: '8px',
            maxWidth: '400px', width: '90%', boxShadow: '0 4px 16px rgba(0,0,0,0.2)'
          }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '16px' }}>确认操作</h3>
            <p style={{ fontSize: '14px' }}>{封禁确认弹窗.提示文本}</p>
            <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button onClick={() => set封禁确认弹窗({ show: false, ids: [], 提示文本: '', 目标状态: 1 })}
                style={{ padding: '8px 20px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                取消
              </button>
              <button onClick={封禁确认执行}
                style={{ padding: '8px 20px', backgroundColor: '#ffc107', color: '#333', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                确认
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminUsers;
