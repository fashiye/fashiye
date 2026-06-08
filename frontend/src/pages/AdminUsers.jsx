import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import './AdminDashboard.css';

const AdminUsers = () => {
  const [用户列表, set用户列表] = useState([]);
  const [加载中, set加载中] = useState(true);
  const [当前页, set当前页] = useState(1);
  const [总页数, set总页数] = useState(1);
  const [总条数, set总条数] = useState(0);
  const 每页条数 = 10;

  useEffect(() => {
    获取用户列表();
  }, [当前页]);

  const 获取用户列表 = async () => {
    set加载中(true);
    try {
      const 响应 = await api.get('/admin/users', { params: { page: 当前页, size: 每页条数 } });
      set用户列表(响应.data.items);
      set总页数(响应.data.pages);
      set总条数(响应.data.total);
    } catch (错误) {
      console.error('获取用户列表失败:', 错误);
    } finally {
      set加载中(false);
    }
  };

  const 处理封禁解禁 = async (用户id, 用户名, 当前状态) => {
    const 操作文本 = 当前状态 === 1 ? '封禁' : '解禁';
    if (!window.confirm(`确定${操作文本}用户 "${用户名}" 吗？${操作文本 === '封禁' ? '被封禁用户无法登录系统。' : ''}`)) return;
    try {
      const 响应 = await api.put(`/admin/users/${用户id}/ban`);
      alert(响应.data.message || `${操作文本}成功`);
      获取用户列表();
    } catch (错误) {
      alert(`${操作文本}失败: ${错误.response?.data?.detail || '未知错误'}`);
    }
  };

  const 处理删除用户 = async (用户id, 用户名) => {
    if (!window.confirm(`确定要删除用户 "${用户名}" 吗？此操作不可恢复！`)) return;
    try {
      await api.delete(`/users/${用户id}?role=user`);
      alert('用户删除成功！');
      获取用户列表();
    } catch (错误) {
      alert(`删除失败: ${错误.response?.data?.detail || '未知错误'}`);
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
    <div className="dashboard-container admin-dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>用户管理</h1>
        </div>
        <div className="header-right">
          <button className="logout-btn" onClick={() => window.history.back()}>返回</button>
        </div>
      </header>

      <main className="dashboard-content">
        <div style={{ marginBottom: '15px', color: '#666', fontSize: '14px' }}>
          共 {总条数} 条记录
        </div>

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
                  <th>状态</th>
                  <th>创建时间</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {用户列表.map(用户 => (
                  <tr key={用户.id}>
                    <td>{用户.id}</td>
                    <td>{用户.username}</td>
                    <td>{用户.email}</td>
                    <td>
                      <span style={{
                        padding: '3px 8px', borderRadius: '3px', fontSize: '13px',
                        backgroundColor: 用户.status === 1 ? '#d4edda' : '#f8d7da',
                        color: 用户.status === 1 ? '#155724' : '#721c24'
                      }}>
                        {用户.status === 1 ? '正常' : '已封禁'}
                      </span>
                    </td>
                    <td>{new Date(用户.createdAt).toLocaleString()}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '5px' }}>
                        <button
                          onClick={() => 处理封禁解禁(用户.id, 用户.username, 用户.status)}
                          style={{
                            padding: '5px 12px',
                            backgroundColor: 用户.status === 1 ? '#ffc107' : '#17a2b8',
                            color: 用户.status === 1 ? '#333' : 'white',
                            border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '13px'
                          }}
                        >
                          {用户.status === 1 ? '封禁' : '解禁'}
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
    </div>
  );
};

export default AdminUsers;
