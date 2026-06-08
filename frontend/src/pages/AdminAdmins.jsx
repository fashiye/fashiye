import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import './AdminDashboard.css';

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

  const 获取管理员列表 = async () => {
    set加载中(true);
    try {
      const 响应 = await api.get('/admin/admins', { params: { page: 当前页, size: 每页条数 } });
      set管理员列表(响应.data.items);
      set总页数(响应.data.pages);
      set总条数(响应.data.total);
    } catch (错误) {
      console.error('获取管理员列表失败:', 错误);
    } finally {
      set加载中(false);
    }
  };

  const 处理创建管理员 = async () => {
    if (!新建用户名.trim() || !新建邮箱.trim() || !新建密码.trim()) {
      alert('请填写完整信息');
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
      alert('管理员创建成功');
      set显示创建弹窗(false);
      set新建用户名('');
      set新建邮箱('');
      set新建密码('');
      set新建权限([]);
      获取管理员列表();
    } catch (错误) {
      alert(`创建失败: ${错误.response?.data?.detail || '未知错误'}`);
    } finally {
      set创建中(false);
    }
  };

  const 处理删除管理员 = async (管理员id, 用户名) => {
    if (!window.confirm(`确定要删除管理员 "${用户名}" 吗？`)) return;
    try {
      await api.delete(`/admin/admins/${管理员id}`);
      alert('删除成功');
      获取管理员列表();
    } catch (错误) {
      alert(`删除失败: ${错误.response?.data?.detail || '未知错误'}`);
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
      alert('权限已更新');
      set显示权限弹窗(null);
      获取管理员列表();
    } catch (错误) {
      alert(`权限更新失败: ${错误.response?.data?.detail || '未知错误'}`);
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
    <div className="dashboard-container admin-dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>管理员管理</h1>
        </div>
        <div className="header-right">
          <button
            onClick={() => set显示创建弹窗(true)}
            style={{
              padding: '8px 20px', backgroundColor: '#28a745', color: 'white',
              border: 'none', borderRadius: '4px', cursor: 'pointer', marginRight: '10px'
            }}
          >
            + 新建管理员
          </button>
          <button className="logout-btn" onClick={() => window.history.back()}>返回</button>
        </div>
      </header>

      <main className="dashboard-content">
        {加载中 ? (
          <div className="loading">加载中...</div>
        ) : (
          <div className="users-list">
            <table className="data-table">
              <thead>
                <tr>
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
                  <tr key={管理员.id}>
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
              </div>
            )}
          </div>
        )}
      </main>

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
