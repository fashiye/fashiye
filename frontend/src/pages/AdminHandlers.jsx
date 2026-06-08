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
  const [编辑等级弹窗, set编辑等级弹窗] = useState(null);
  const [新等级, set新等级] = useState(1);
  const 每页条数 = 10;

  useEffect(() => {
    获取打手列表();
  }, [当前页, 状态筛选]);

  const 获取打手列表 = async () => {
    set加载中(true);
    try {
      const params = { page: 当前页, size: 每页条数 };
      if (状态筛选) {
        params.status = 状态筛选;
      }
      const 响应 = await api.get('/admin/handlers', { params });
      set打手列表(响应.data.items);
      set总页数(响应.data.pages);
      set总条数(响应.data.total);
    } catch (错误) {
      console.error('获取打手列表失败:', 错误);
    } finally {
      set加载中(false);
    }
  };

  const 处理审核通过 = async (打手id, 用户名) => {
    if (!window.confirm(`确定审核通过打手 "${用户名}" 吗？`)) return;
    try {
      await api.post(`/admin/handlers/${打手id}/approve`);
      alert('审核通过成功');
      获取打手列表();
    } catch (错误) {
      alert(`审核失败: ${错误.response?.data?.detail || '未知错误'}`);
    }
  };

  const 处理审核拒绝 = async (打手id, 用户名) => {
    if (!window.confirm(`确定拒绝打手 "${用户名}" 的注册申请吗？`)) return;
    try {
      await api.post(`/admin/handlers/${打手id}/reject`);
      alert('已拒绝该申请');
      获取打手列表();
    } catch (错误) {
      alert(`操作失败: ${错误.response?.data?.detail || '未知错误'}`);
    }
  };

  const 处理封禁解禁 = async (打手id, 用户名, 当前状态) => {
    const 操作文本 = 当前状态 === 1 ? '封禁' : '解禁';
    if (!window.confirm(`确定${操作文本}打手 "${用户名}" 吗？`)) return;
    try {
      await api.put(`/admin/handlers/${打手id}/ban`);
      alert(`${操作文本}成功`);
      获取打手列表();
    } catch (错误) {
      alert(`${操作文本}失败: ${错误.response?.data?.detail || '未知错误'}`);
    }
  };

  const 处理删除 = async (打手id, 用户名) => {
    if (!window.confirm(`确定要删除打手 "${用户名}" 吗？此操作不可恢复！`)) return;
    try {
      await api.delete(`/users/${打手id}?role=handler`);
      alert('删除成功');
      获取打手列表();
    } catch (错误) {
      alert(`删除失败: ${错误.response?.data?.detail || '未知错误'}`);
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
      alert('等级已更新');
      set编辑等级弹窗(null);
      获取打手列表();
    } catch (错误) {
      alert(`等级更新失败: ${错误.response?.data?.detail || '未知错误'}`);
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
          <h1>打手管理</h1>
        </div>
        <div className="header-right">
          <button className="logout-btn" onClick={() => window.history.back()}>返回</button>
        </div>
      </header>

      <main className="dashboard-content">
        <div style={{ marginBottom: '20px' }}>
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
          <span style={{ marginLeft: '15px', color: '#666', fontSize: '14px' }}>共 {总条数} 条记录</span>
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
                  <tr key={打手.id}>
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
                          onClick={() => 处理删除(打手.id, 打手.username)}
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
              </div>
            )}
          </div>
        )}
      </main>

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
