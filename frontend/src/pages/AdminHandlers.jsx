import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import './AdminDashboard.css';

const 打手状态文本 = {
  0: { text: '待审核', class: 'status-pending' },
  1: { text: '正常', class: 'status-active' },
  2: { text: '未通过', class: 'status-rejected' },
  3: { text: '已封禁', class: 'status-banned' }
};

const AdminHandlers = () => {
  const [打手列表, set打手列表] = useState([]);
  const [加载中, set加载中] = useState(true);
  const [当前页, set当前页] = useState(1);
  const [总页数, set总页数] = useState(1);
  const [总条数, set总条数] = useState(0);
  const [状态筛选, set状态筛选] = useState('');
  const [选中ID集合, set选中ID集合] = useState(new Set());
  const [删除确认弹窗, set删除确认弹窗] = useState({ show: false, ids: [], 提示文本: '' });
  const [编辑等级弹窗, set编辑等级弹窗] = useState(null);
  const [新等级, set新等级] = useState(1);
  const [提示, set提示] = useState({ show: false, type: 'success', message: '' });
  const 每页条数 = 10;

  useEffect(() => {
    获取打手列表();
  }, [当前页, 状态筛选]);

  useEffect(() => {
    if (提示.show) {
      const 定时器 = setTimeout(() => set提示({ show: false, type: '', message: '' }), 3000);
      return () => clearTimeout(定时器);
    }
  }, [提示.show]);

  const 显示提示 = (message, type = 'success') => {
    set提示({ show: true, type, message });
  };

  const 获取打手列表 = async () => {
    set加载中(true);
    try {
      const params = { page: 当前页, size: 每页条数 };
      if (状态筛选) {
        params.status = 状态筛选;
      }
      const 响应 = await api.get('/admin/handlers', { params });
      set打手列表(响应.data.data.items);
      set总页数(Math.ceil((响应.data.data.total || 0) / 每页条数));
      set总条数(响应.data.data.total);
    } catch (错误) {
      console.error('获取打手列表失败:', 错误);
      显示提示('获取打手列表失败', 'error');
    } finally {
      set加载中(false);
    }
  };

  // 全选/取消全选
  const 切换全选 = () => {
    if (选中ID集合.size === 打手列表.length) {
      set选中ID集合(new Set());
    } else {
      set选中ID集合(new Set(打手列表.map(h => h.id)));
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

  const 处理审核通过 = async (打手id, 用户名) => {
    set删除确认弹窗({
      show: true,
      ids: [],
      提示文本: `确定审核通过打手 "${用户名}" 吗？`,
      操作类型: 'approve',
      操作ID: 打手id
    });
  };

  const 审核确认执行 = async () => {
    const { 操作类型, 操作ID } = 删除确认弹窗;
    try {
      if (操作类型 === 'approve') {
        await api.post(`/admin/handlers/${操作ID}/approve`);
      } else if (操作类型 === 'reject') {
        await api.post(`/admin/handlers/${操作ID}/reject`);
      }
      显示提示(操作类型 === 'approve' ? '审核通过成功' : '已拒绝该申请');
      set删除确认弹窗({ show: false, ids: [], 提示文本: '' });
      获取打手列表();
    } catch (错误) {
      显示提示(`操作失败: ${错误.response?.data?.detail || '未知错误'}`, 'error');
    }
  };

  const 处理审核拒绝 = async (打手id, 用户名) => {
    set删除确认弹窗({
      show: true,
      ids: [],
      提示文本: `确定拒绝打手 "${用户名}" 的注册申请吗？`,
      操作类型: 'reject',
      操作ID: 打手id
    });
  };

  const 处理封禁解禁 = async (打手id, 用户名, 当前状态) => {
    const 操作文本 = 当前状态 === 1 ? '封禁' : '解禁';
    set删除确认弹窗({
      show: true,
      ids: [],
      提示文本: `确定${操作文本}打手 "${用户名}" 吗？`,
      操作类型: 'toggleStatus',
      操作ID: 打手id,
      目标状态: 当前状态 === 1 ? 3 : 1
    });
  };

  const 状态切换确认执行 = async () => {
    const { 操作ID, 目标状态 } = 删除确认弹窗;
    try {
      await api.put(`/admin/handlers/${操作ID}/status`, { status: 目标状态 });
      const 操作文本 = 目标状态 === 3 ? '封禁' : '解禁';
      显示提示(`${操作文本}成功`);
      set删除确认弹窗({ show: false, ids: [], 提示文本: '' });
      获取打手列表();
    } catch (错误) {
      显示提示(`操作失败: ${错误.response?.data?.detail || '未知错误'}`, 'error');
    }
  };

  const 处理删除打手 = (打手id, 用户名) => {
    set删除确认弹窗({
      show: true,
      ids: [打手id],
      提示文本: `确定要删除打手 "${用户名}" 吗？此操作不可恢复！`,
      操作类型: 'delete'
    });
  };

  const 处理批量删除 = () => {
    if (选中ID集合.size === 0) return;
    set删除确认弹窗({
      show: true,
      ids: [...选中ID集合],
      提示文本: `确定要删除选中的 ${选中ID集合.size} 个打手吗？此操作不可恢复！`,
      操作类型: 'batchDelete'
    });
  };

  const 删除确认执行 = async () => {
    const { ids, 操作类型 } = 删除确认弹窗;
    try {
      if (操作类型 === 'delete' || 操作类型 === 'batchDelete') {
        await Promise.all(ids.map(id => api.delete(`/admin/users/${id}`)));
        set选中ID集合(new Set());
        显示提示(`成功删除 ${ids.length} 个打手`);
      }
      set删除确认弹窗({ show: false, ids: [], 提示文本: '' });
      获取打手列表();
    } catch (错误) {
      显示提示(`删除失败: ${错误.response?.data?.detail || '未知错误'}`, 'error');
    }
  };

  const 打开等级编辑 = (打手) => {
    set新等级(打手.level);
    set编辑等级弹窗(打手);
  };

  const 提交等级修改 = async () => {
    if (!编辑等级弹窗) return;
    try {
      await api.put(`/admin/handlers/${编辑等级弹窗.id}/level`, { level: 新等级 });
      显示提示('等级已更新');
      set编辑等级弹窗(null);
      获取打手列表();
    } catch (错误) {
      显示提示(`等级更新失败: ${错误.response?.data?.detail || '未知错误'}`, 'error');
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

  // 判断确认弹窗的类型
  const 当前弹窗标题 = () => {
    const 类型 = 删除确认弹窗.操作类型;
    if (类型 === 'approve') return '审核通过';
    if (类型 === 'reject') return '拒绝申请';
    if (类型 === 'toggleStatus') return '确认操作';
    return '确认删除';
  };

  const 当前弹窗确认按钮 = () => {
    const 类型 = 删除确认弹窗.操作类型;
    if (类型 === 'delete' || 类型 === 'batchDelete') {
      return { text: '确认删除', color: '#dc3545' };
    }
    return { text: '确认', color: '#ffc107' };
  };

  const 弹窗确认执行 = () => {
    const 类型 = 删除确认弹窗.操作类型;
    if (类型 === 'approve' || 类型 === 'reject') {
      审核确认执行();
    } else if (类型 === 'toggleStatus') {
      状态切换确认执行();
    } else {
      删除确认执行();
    }
  };

  return (
    <div className="dashboard-container admin-dashboard">
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

      <header className="dashboard-header">
        <div className="header-left">
          <h1>打手管理</h1>
        </div>
        <div className="header-right">
          <button className="logout-btn" onClick={() => window.history.back()}>返回</button>
        </div>
      </header>

      <main className="dashboard-content">
        <div style={{ marginBottom: '15px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
            <select
              value={状态筛选}
              onChange={(e) => { set状态筛选(e.target.value); set当前页(1); }}
              style={{ padding: '8px 16px', borderRadius: '4px', border: '1px solid #ddd', fontSize: '14px' }}
            >
              <option value="">全部打手</option>
              <option value="0">待审核</option>
              <option value="1">正常</option>
              <option value="2">未通过</option>
              <option value="3">已封禁</option>
            </select>
            <span style={{ color: '#666', fontSize: '14px' }}>
              共 {总条数} 条记录
              {选中ID集合.size > 0 && (
                <span style={{ marginLeft: '10px', color: '#007bff' }}>
                  （已选 {选中ID集合.size} 项）
                </span>
              )}
            </span>
          </div>
          {选中ID集合.size > 0 && (
            <button
              onClick={处理批量删除}
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
          <div className="loading">加载中...</div>
        ) : (
          <div className="users-list">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: '40px' }}>
                    <input
                      type="checkbox"
                      checked={打手列表.length > 0 && 选中ID集合.size === 打手列表.length}
                      onChange={切换全选}
                      style={{ cursor: 'pointer' }}
                    />
                  </th>
                  <th>ID</th>
                  <th>用户名</th>
                  <th>邮箱</th>
                  <th>等级</th>
                  <th>状态</th>
                  <th>接单数</th>
                  <th>完成率</th>
                  <th>注册时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {打手列表.map(打手 => (
                  <tr key={打手.id} style={{
                    backgroundColor: 选中ID集合.has(打手.id) ? '#f0f7ff' : 'transparent'
                  }}>
                    <td>
                      <input
                        type="checkbox"
                        checked={选中ID集合.has(打手.id)}
                        onChange={() => 切换选中(打手.id)}
                        style={{ cursor: 'pointer' }}
                      />
                    </td>
                    <td>{打手.id}</td>
                    <td>{打手.username}</td>
                    <td>{打手.email}</td>
                    <td>
                      {打手.level}
                      {打手.status === 1 && (
                        <button
                          onClick={() => 打开等级编辑(打手)}
                          style={{
                            marginLeft: '8px', padding: '2px 8px', fontSize: '12px',
                            backgroundColor: '#ffc107', color: '#333', border: 'none',
                            borderRadius: '3px', cursor: 'pointer'
                          }}
                        >
                          调整
                        </button>
                      )}
                    </td>
                    <td>
                      <span style={{
                        padding: '3px 8px', borderRadius: '3px', fontSize: '13px',
                        backgroundColor: 打手.status === 0 ? '#fff3cd' :
                                          打手.status === 1 ? '#d4edda' :
                                          打手.status === 2 ? '#f8d7da' : '#e2e3e5',
                        color: 打手.status === 0 ? '#856404' :
                                打手.status === 1 ? '#155724' :
                                打手.status === 2 ? '#721c24' : '#383d41'
                      }}>
                        {打手状态文本[打手.status]?.text || '未知'}
                      </span>
                    </td>
                    <td>{打手.totalOrders}</td>
                    <td>{打手.completionRate}%</td>
                    <td>{new Date(打手.createdAt).toLocaleString()}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                        {打手.status === 0 && (
                          <>
                            <button
                              onClick={() => 处理审核通过(打手.id, 打手.username)}
                              style={{
                                padding: '5px 12px', backgroundColor: '#28a745', color: 'white',
                                border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px'
                              }}
                            >
                              通过
                            </button>
                            <button
                              onClick={() => 处理审核拒绝(打手.id, 打手.username)}
                              style={{
                                padding: '5px 12px', backgroundColor: '#dc3545', color: 'white',
                                border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px'
                              }}
                            >
                              拒绝
                            </button>
                          </>
                        )}
                        {打手.status === 1 && (
                          <button
                            onClick={() => 处理封禁解禁(打手.id, 打手.username, 打手.status)}
                            style={{
                              padding: '5px 12px', backgroundColor: '#ffc107', color: '#333',
                              border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px'
                            }}
                          >
                            封禁
                          </button>
                        )}
                        {打手.status === 3 && (
                          <button
                            onClick={() => 处理封禁解禁(打手.id, 打手.username, 打手.status)}
                            style={{
                              padding: '5px 12px', backgroundColor: '#17a2b8', color: 'white',
                              border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px'
                            }}
                          >
                            解禁
                          </button>
                        )}
                        <button
                          onClick={() => 处理删除打手(打手.id, 打手.username)}
                          style={{
                            padding: '5px 12px', backgroundColor: '#6c757d', color: 'white',
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
      </main>

      {/* 统一确认弹窗（覆盖删除/审核/封禁） */}
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
            <h3 style={{ margin: '0 0 12px 0', fontSize: '16px' }}>{当前弹窗标题()}</h3>
            <p style={{ fontSize: '14px' }}>{删除确认弹窗.提示文本}</p>
            {(删除确认弹窗.操作类型 === 'delete' || 删除确认弹窗.操作类型 === 'batchDelete') && (
              <p style={{ color: '#999', fontSize: '13px', margin: '8px 0 0 0' }}>此操作不可恢复</p>
            )}
            <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                onClick={() => set删除确认弹窗({ show: false, ids: [], 提示文本: '' })}
                style={{
                  padding: '8px 20px', backgroundColor: '#6c757d', color: 'white',
                  border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '14px'
                }}
              >
                取消
              </button>
              <button
                onClick={弹窗确认执行}
                style={{
                  padding: '8px 20px',
                  backgroundColor: 当前弹窗确认按钮().color,
                  color: 当前弹窗确认按钮().text === '确认删除' ? 'white' : '#333',
                  border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '14px'
                }}
              >
                {当前弹窗确认按钮().text}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 等级编辑弹窗 */}
      {编辑等级弹窗 && (
        <div
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex',
            justifyContent: 'center', alignItems: 'center', zIndex: 1000
          }}
          onClick={() => set编辑等级弹窗(null)}
        >
          <div
            style={{
              backgroundColor: 'white', padding: '30px', borderRadius: '8px',
              minWidth: '350px', maxWidth: '500px'
            }}
            onClick={e => e.stopPropagation()}
          >
            <h3 style={{ marginBottom: '20px' }}>调整打手等级 - {编辑等级弹窗.username}</h3>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>等级</label>
              <input
                type="number"
                min="1"
                max="100"
                value={新等级}
                onChange={(e) => set新等级(parseInt(e.target.value) || 1)}
                style={{
                  width: '100%', padding: '10px', border: '1px solid #ddd',
                  borderRadius: '4px', fontSize: '16px', boxSizing: 'border-box'
                }}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                onClick={() => set编辑等级弹窗(null)}
                style={{
                  padding: '8px 20px', backgroundColor: '#6c757d', color: 'white',
                  border: 'none', borderRadius: '4px', cursor: 'pointer'
                }}
              >
                取消
              </button>
              <button
                onClick={提交等级修改}
                style={{
                  padding: '8px 20px', backgroundColor: '#007bff', color: 'white',
                  border: 'none', borderRadius: '4px', cursor: 'pointer'
                }}
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminHandlers;
