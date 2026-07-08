import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import 样式 from './AdminDashboard.module.css';

const 功能权限选项 = [
  { key: 'order_management', label: '订单管理' },
  { key: 'order_review', label: '订单审核' },
  { key: 'game_management', label: '游戏管理' },
  { key: 'system_settings', label: '系统设置' },
  { key: 'database_management', label: '数据库管理' },
  { key: 'message_management', label: '消息管理' }
];

const AdminAdmins = () => {
  const [管理员列表, set管理员列表] = useState([]);
  const [加载中, set加载中] = useState(true);
  const [当前页, set当前页] = useState(1);
  const [总页数, set总页数] = useState(1);
  const [总条数, set总条数] = useState(0);
  const [选中ID集合, set选中ID集合] = useState(new Set());
  const [删除确认弹窗, set删除确认弹窗] = useState({ show: false, ids: [], 提示文本: '' });
  const [提示, set提示] = useState({ show: false, type: 'success', message: '' });

  const [显示创建弹窗, set显示创建弹窗] = useState(false);
  const [新建用户名, set新建用户名] = useState('');
  const [新建邮箱, set新建邮箱] = useState('');
  const [新建密码, set新建密码] = useState('');
  const [新建权限, set新建权限] = useState([]);

  const [显示权限弹窗, set显示权限弹窗] = useState(null);
  const [编辑权限, set编辑权限] = useState([]);
  const [创建中, set创建中] = useState(false);
  const 每页条数 = 10;

  useEffect(() => {
    获取管理员列表();
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

  const 获取管理员列表 = async () => {
    set加载中(true);
    try {
      const 响应 = await api.get('/admin/admins', { params: { page: 当前页, size: 每页条数 } });
      set管理员列表(响应.data.data.items);
      set总页数(响应.data.data.pages);
      set总条数(响应.data.data.total);
    } catch (错误) {
      console.error('获取管理员列表失败:', 错误);
      显示提示('获取管理员列表失败', 'error');
    } finally {
      set加载中(false);
    }
  };

  // 全选/取消全选
  const 切换全选 = () => {
    const 可删管理员 = 管理员列表.filter(a => a.role !== 'super');
    if (可删管理员.length > 0 && 选中ID集合.size === 可删管理员.length) {
      set选中ID集合(new Set());
    } else {
      set选中ID集合(new Set(可删管理员.map(a => a.id)));
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

  const 处理创建管理员 = async () => {
    if (!新建用户名.trim() || !新建邮箱.trim() || !新建密码.trim()) {
      显示提示('请填写完整信息', 'error');
      return;
    }
    set创建中(true);
    try {
      await api.post('/admin/admins', {
        username: 新建用户名,
        email: 新建邮箱,
        password: 新建密码,
        permissions: 新建权限
      });
      显示提示('管理员创建成功');
      set显示创建弹窗(false);
      set新建用户名('');
      set新建邮箱('');
      set新建密码('');
      set新建权限([]);
      获取管理员列表();
    } catch (错误) {
      显示提示(`创建失败: ${错误.response?.data?.detail || '未知错误'}`, 'error');
    } finally {
      set创建中(false);
    }
  };

  const 处理删除管理员 = (管理员id, 用户名) => {
    set删除确认弹窗({
      show: true,
      ids: [管理员id],
      提示文本: `确定要删除管理员 "${用户名}" 吗？`
    });
  };

  const 处理批量删除 = () => {
    if (选中ID集合.size === 0) return;
    set删除确认弹窗({
      show: true,
      ids: [...选中ID集合],
      提示文本: `确定要删除选中的 ${选中ID集合.size} 个管理员吗？`
    });
  };

  const 删除确认执行 = async () => {
    const { ids } = 删除确认弹窗;
    try {
      await Promise.all(ids.map(id => api.delete(`/admin/admins/${id}`)));
      set选中ID集合(new Set());
      set删除确认弹窗({ show: false, ids: [], 提示文本: '' });
      显示提示(`成功删除 ${ids.length} 个管理员`);
      获取管理员列表();
    } catch (错误) {
      显示提示(`删除失败: ${错误.response?.data?.detail || '未知错误'}`, 'error');
    }
  };

  const 打开权限编辑 = async (管理员) => {
    set显示权限弹窗(管理员);
    try {
      const 响应 = await api.get(`/admin/admins/${管理员.id}/permissions`);
      set编辑权限(响应.data.data.permissions || []);
    } catch (错误) {
      console.error('获取权限信息失败:', 错误);
      set编辑权限(管理员.permissions || []);
    }
  };

  const 提交权限修改 = async () => {
    if (!显示权限弹窗) return;
    try {
      await api.put(`/admin/admins/${显示权限弹窗.id}/permissions`, { permissions: 编辑权限 });
      显示提示('权限已更新');
      set显示权限弹窗(null);
      获取管理员列表();
    } catch (错误) {
      显示提示(`权限更新失败: ${错误.response?.data?.detail || '未知错误'}`, 'error');
    }
  };

  const 切换权限选择 = (权限键) => {
    set编辑权限(prev =>
      prev.includes(权限键) ? prev.filter(k => k !== 权限键) : [...prev, 权限键]
    );
  };

  const 切换新建权限 = (权限键) => {
    set新建权限(prev =>
      prev.includes(权限键) ? prev.filter(k => k !== 权限键) : [...prev, 权限键]
    );
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
          <h1>管理员管理</h1>
        </div>
        <div className={样式.headerRight}>
          <button
            onClick={() => set显示创建弹窗(true)}
            style={{
              padding: '8px 20px', backgroundColor: '#28a745', color: 'white',
              border: 'none', borderRadius: '4px', cursor: 'pointer', marginRight: '10px'
            }}
          >
            + 新建管理员
          </button>
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
          <div className={样式.loading}>加载中...</div>
        ) : (
          <div className={样式.usersList}>
            <table className={样式.dataTable}>
              <thead>
                <tr>
                  <th style={{ width: '40px' }}>
                    <input
                      type="checkbox"
                      checked={管理员列表.filter(a => a.role !== 'super').length > 0 && 选中ID集合.size === 管理员列表.filter(a => a.role !== 'super').length}
                      onChange={切换全选}
                      style={{ cursor: 'pointer' }}
                    />
                  </th>
                  <th>ID</th>
                  <th>用户名</th>
                  <th>邮箱</th>
                  <th>角色</th>
                  <th>状态</th>
                  <th>功能权限</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {管理员列表.map(管理员 => (
                  <tr key={管理员.id} style={{
                    backgroundColor: 选中ID集合.has(管理员.id) ? '#f0f7ff' : 'transparent',
                    opacity: 管理员.role === 'super' ? 0.7 : 1
                  }}>
                    <td>
                      {管理员.role !== 'super' && (
                        <input
                          type="checkbox"
                          checked={选中ID集合.has(管理员.id)}
                          onChange={() => 切换选中(管理员.id)}
                          style={{ cursor: 'pointer' }}
                        />
                      )}
                    </td>
                    <td>{管理员.id}</td>
                    <td>{管理员.username}</td>
                    <td>{管理员.email}</td>
                    <td>
                      <span style={{
                        padding: '3px 8px', borderRadius: '3px', fontSize: '13px',
                        backgroundColor: 管理员.role === 'super' ? '#cce5ff' : '#e2e3e5',
                        color: 管理员.role === 'super' ? '#004085' : '#383d41'
                      }}>
                        {管理员.role === 'super' ? '超级管理员' : '普通管理员'}
                      </span>
                    </td>
                    <td>{管理员.status === 1 ? '正常' : '禁用'}</td>
                    <td style={{ maxWidth: '200px' }}>
                      {管理员.role === 'super' ? (
                        <span style={{ color: '#999', fontSize: '13px' }}>全部权限</span>
                      ) : (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px' }}>
                          {管理员.permissions && 管理员.permissions.length > 0 ? (
                            管理员.permissions.map(p => {
                              const 选项 = 功能权限选项.find(o => o.key === p);
                              return 选项 ? (
                                <span key={p} style={{
                                  padding: '2px 6px', backgroundColor: '#e8f5e9',
                                  borderRadius: '3px', fontSize: '12px', color: '#2e7d32'
                                }}>
                                  {选项.label}
                                </span>
                              ) : null;
                            })
                          ) : (
                            <span style={{ color: '#999', fontSize: '12px' }}>无权限</span>
                          )}
                        </div>
                      )}
                    </td>
                    <td>{new Date(管理员.createdAt).toLocaleString()}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '5px' }}>
                        {管理员.role !== 'super' && (
                          <>
                            <button
                              onClick={() => 打开权限编辑(管理员)}
                              style={{
                                padding: '5px 12px', backgroundColor: '#007bff', color: 'white',
                                border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px'
                              }}
                            >
                              权限
                            </button>
                            <button
                              onClick={() => 处理删除管理员(管理员.id, 管理员.username)}
                              style={{
                                padding: '5px 12px', backgroundColor: '#dc3545', color: 'white',
                                border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px'
                              }}
                            >
                              删除
                            </button>
                          </>
                        )}
                        {管理员.role === 'super' && (
                          <span style={{ color: '#999', fontSize: '13px' }}>-</span>
                        )}
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
              <button
                onClick={() => set删除确认弹窗({ show: false, ids: [], 提示文本: '' })}
                style={{ padding: '8px 20px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '14px' }}
              >
                取消
              </button>
              <button
                onClick={删除确认执行}
                style={{ padding: '8px 20px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '14px' }}
              >
                确认删除
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 创建管理员弹窗 */}
      {显示创建弹窗 && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex',
          justifyContent: 'center', alignItems: 'center', zIndex: 1000
        }} onClick={() => set显示创建弹窗(false)}>
          <div style={{
            backgroundColor: 'white', padding: '30px', borderRadius: '8px',
            minWidth: '450px', maxWidth: '550px'
          }} onClick={e => e.stopPropagation()}>
            <h3 style={{ marginBottom: '20px' }}>新建管理员</h3>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>用户名</label>
              <input type="text" value={新建用户名} onChange={e => set新建用户名(e.target.value)}
                style={{ width: '100%', padding: '10px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '14px', boxSizing: 'border-box' }} />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>邮箱</label>
              <input type="email" value={新建邮箱} onChange={e => set新建邮箱(e.target.value)}
                style={{ width: '100%', padding: '10px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '14px', boxSizing: 'border-box' }} />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>密码</label>
              <input type="password" value={新建密码} onChange={e => set新建密码(e.target.value)}
                style={{ width: '100%', padding: '10px', border: '1px solid #ddd', borderRadius: '4px', fontSize: '14px', boxSizing: 'border-box' }} />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>功能权限</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {功能权限选项.map(选项 => (
                  <label key={选项.key} style={{
                    display: 'flex', alignItems: 'center', gap: '5px',
                    padding: '6px 12px', border: '1px solid #ddd', borderRadius: '4px',
                    cursor: 'pointer', backgroundColor: 新建权限.includes(选项.key) ? '#e8f5e9' : 'white',
                    userSelect: 'none', fontSize: '14px'
                  }}>
                    <input
                      type="checkbox"
                      checked={新建权限.includes(选项.key)}
                      onChange={() => 切换新建权限(选项.key)}
                      style={{ margin: 0 }}
                    />
                    {选项.label}
                  </label>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button onClick={() => set显示创建弹窗(false)}
                style={{ padding: '8px 20px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                取消
              </button>
              <button onClick={处理创建管理员} disabled={创建中}
                style={{ padding: '8px 20px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 创建中 ? 'not-allowed' : 'pointer' }}>
                {创建中 ? '创建中...' : '创建'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 权限编辑弹窗 */}
      {显示权限弹窗 && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex',
          justifyContent: 'center', alignItems: 'center', zIndex: 1000
        }} onClick={() => set显示权限弹窗(null)}>
          <div style={{
            backgroundColor: 'white', padding: '30px', borderRadius: '8px',
            minWidth: '450px', maxWidth: '550px'
          }} onClick={e => e.stopPropagation()}>
            <h3 style={{ marginBottom: '10px' }}>设置功能权限 - {显示权限弹窗.username}</h3>
            <p style={{ color: '#666', marginBottom: '20px', fontSize: '14px' }}>
              选择该管理员可以访问的功能模块
            </p>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '20px' }}>
              {功能权限选项.map(选项 => (
                <label key={选项.key} style={{
                  display: 'flex', alignItems: 'center', gap: '5px',
                  padding: '8px 14px', border: '1px solid #ddd', borderRadius: '4px',
                  cursor: 'pointer', backgroundColor: 编辑权限.includes(选项.key) ? '#e8f5e9' : 'white',
                  userSelect: 'none', fontSize: '14px'
                }}>
                  <input
                    type="checkbox"
                    checked={编辑权限.includes(选项.key)}
                    onChange={() => 切换权限选择(选项.key)}
                    style={{ margin: 0 }}
                  />
                  {选项.label}
                </label>
              ))}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button onClick={() => set显示权限弹窗(null)}
                style={{ padding: '8px 20px', backgroundColor: '#6c757d', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                取消
              </button>
              <button onClick={提交权限修改}
                style={{ padding: '8px 20px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                保存权限
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminAdmins;
