import React, { useState, useEffect } from 'react';
import api from '../utils/api';
import './AdminDashboard.css';

const AdminUsers = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalUsers, setTotalUsers] = useState(0);
  const pageSize = 10;

  useEffect(() => {
    fetchUsers();
    fetchCurrentUser();
  }, [currentPage]);

  const fetchUsers = async () => {
    try {
      const response = await api.get(`/users?page=${currentPage}&size=${pageSize}`);
      setUsers(response.data.items);
      setTotalPages(response.data.pages);
      setTotalUsers(response.data.total);
    } catch (err) {
      console.error('获取用户列表失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get('/auth/me');
      setCurrentUser(response.data);
    } catch (err) {
      console.error('获取当前用户信息失败:', err);
    }
  };

  const handleDeleteUser = async (userId, username, role) => {
    if (!window.confirm(`确定要删除用户 "${username}" 吗？此操作不可恢复！`)) {
      return;
    }

    try {
      await api.delete(`/users/${userId}?role=${role}`);
      alert('用户删除成功！');
      fetchUsers();
    } catch (err) {
      const errorMsg = err.response?.data?.detail || '删除失败';
      alert(`删除失败: ${errorMsg}`);
    }
  };

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  const renderPagination = () => {
    const pages = [];
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    if (endPage - startPage < maxVisiblePages - 1) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(
        <button
          key={i}
          onClick={() => handlePageChange(i)}
          style={{
            padding: '8px 12px',
            margin: '0 4px',
            border: '1px solid #ddd',
            backgroundColor: i === currentPage ? '#007bff' : 'white',
            color: i === currentPage ? 'white' : '#333',
            cursor: 'pointer',
            borderRadius: '4px'
          }}
        >
          {i}
        </button>
      );
    }

    return pages;
  };

  const isSuperAdmin = currentUser?.role === 'super';

  return (
    <div className="dashboard-container admin-dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>用户管理</h1>
        </div>
        <div className="header-right">
          <button className="logout-btn" onClick={() => window.history.back()}>
            返回
          </button>
        </div>
      </header>
      
      <main className="dashboard-content">
        {loading ? (
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
                  <th>创建时间</th>
                  {isSuperAdmin && <th>操作</th>}
                </tr>
              </thead>
              <tbody>
                {users.map(user => (
                  <tr key={`${user.role}-${user.id}`}>
                    <td>{user.id}</td>
                    <td>{user.username}</td>
                    <td>{user.email}</td>
                    <td>{user.role}</td>
                    <td>{user.status === 1 ? '正常' : '禁用'}</td>
                    <td>{new Date(user.createdAt).toLocaleString()}</td>
                    {isSuperAdmin && (
                      <td>
                        <button
                          className="delete-btn"
                          onClick={() => handleDeleteUser(user.id, user.username, user.role)}
                          style={{
                            padding: '5px 15px',
                            backgroundColor: '#ff4444',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer',
                            fontSize: '14px'
                          }}
                        >
                          删除
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
            
            {totalPages > 1 && (
              <div style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                marginTop: '20px',
                padding: '20px'
              }}>
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  style={{
                    padding: '8px 16px',
                    margin: '0 4px',
                    border: '1px solid #ddd',
                    backgroundColor: currentPage === 1 ? '#f5f5f5' : 'white',
                    color: currentPage === 1 ? '#ccc' : '#333',
                    cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                    borderRadius: '4px'
                  }}
                >
                  上一页
                </button>
                
                {renderPagination()}
                
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  style={{
                    padding: '8px 16px',
                    margin: '0 4px',
                    border: '1px solid #ddd',
                    backgroundColor: currentPage === totalPages ? '#f5f5f5' : 'white',
                    color: currentPage === totalPages ? '#ccc' : '#333',
                    cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                    borderRadius: '4px'
                  }}
                >
                  下一页
                </button>
                
                <span style={{ marginLeft: '20px', color: '#666' }}>
                  共 {totalUsers} 条记录，第 {currentPage}/{totalPages} 页
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
