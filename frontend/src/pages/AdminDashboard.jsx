import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import 样式 from './AdminDashboard.module.css';

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [当前用户, set当前用户] = useState(null);

  useEffect(() => {
    const 获取当前用户 = async () => {
      try {
        const 响应 = await api.get('/users/me');
        const 用户数据 = 响应.data.data;
        set当前用户(用户数据);
      } catch (错误) {
        console.error('获取用户信息失败:', 错误);
      }
    };
    获取当前用户();
  }, []);

  const 处理退出登录 = () => {
    localStorage.clear();
    window.dispatchEvent(new Event('auth-change'));
    navigate('/');
  };

  const 是否超级管理员 = 当前用户?.role === 'super';

  const 菜单卡片 = [
    ...(是否超级管理员 ? [
      { key: 'user_management', 标题: '用户管理', 描述: '管理平台普通用户', 路径: '/admin/users', 颜色: '#007bff' },
      { key: 'handler_management', 标题: '打手管理', 描述: '审核打手注册、调整等级', 路径: '/admin/handlers', 颜色: '#28a745' },
      { key: 'admin_management', 标题: '管理员管理', 描述: '管理管理员账号和权限', 路径: '/admin/admins', 颜色: '#6f42c1' }
    ] : []),
    { key: 'order_management', 标题: '订单管理', 描述: '管理所有订单', 路径: '/admin/orders', 颜色: '#17a2b8' },
    { key: 'order_review', 标题: '订单审核', 描述: '审核待处理订单', 路径: '/admin/order-review', 颜色: '#fd7e14' },
    { key: 'game_management', 标题: '游戏管理', 描述: '管理游戏和项目', 路径: '/admin/games', 颜色: '#20c997' },
    ...(是否超级管理员 ? [
      { key: 'system_settings', 标题: '系统设置', 描述: '平台系统配置', 路径: '/admin/settings', 颜色: '#6c757d' },
      { key: 'database_management', 标题: '数据库管理', 描述: '直接管理数据库表数据', 路径: '/admin/database', 颜色: '#dc3545' }
    ] : [])
  ];

  return (
    <div className={样式.dashboardContainer}>
      <header className={样式.dashboardHeader}>
        <div className={样式.headerLeft}>
          <h1>管理中心</h1>
          <span style={{
            marginLeft: '15px', padding: '3px 10px', borderRadius: '4px', fontSize: '13px',
            backgroundColor: 是否超级管理员 ? '#cce5ff' : '#e2e3e5',
            color: 是否超级管理员 ? '#004085' : '#383d41'
          }}>
            {是否超级管理员 ? '超级管理员' : '普通管理员'}
          </span>
        </div>
        <div className={样式.headerRight}>
          <button
            onClick={() => navigate(`/admin/account`)}
            style={{
              padding: '8px 16px', backgroundColor: 'transparent', color: '#333',
              border: '1px solid #ddd', borderRadius: '4px', cursor: 'pointer', marginRight: '10px'
            }}
          >
            账户管理
          </button>
          <button className={样式.logoutBtn} onClick={处理退出登录}>退出登录</button>
        </div>
      </header>

      <main className={样式.dashboardContent}>
        <div className={样式.dashboardGrid}>
          {菜单卡片.map(卡片 => (
            <div className={样式.dashboardCard} key={卡片.key}>
              <h3>{卡片.标题}</h3>
              <p>{卡片.描述}</p>
              <button
                className={样式.cardBtn}
                onClick={() => navigate(卡片.路径)}
                style={{ backgroundColor: 卡片.颜色, color: 'white' }}
              >
                进入
              </button>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default AdminDashboard;
