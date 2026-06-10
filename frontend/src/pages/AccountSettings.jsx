import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import './AccountSettings.css';

const AccountSettings = () => {
  const navigate = useNavigate();
  const role = localStorage.getItem('role');

  const [用户信息, set用户信息] = useState(null);
  const [加载中, set加载中] = useState(true);

  const [昵称弹窗, set昵称弹窗] = useState(false);
  const [新昵称, set新昵称] = useState('');
  const [昵称提交中, set昵称提交中] = useState(false);

  const [密码弹窗, set密码弹窗] = useState(false);
  const [旧密码, set旧密码] = useState('');
  const [新密码, set新密码] = useState('');
  const [确认密码, set确认密码] = useState('');
  const [密码提交中, set密码提交中] = useState(false);

  const [提示消息, set提示消息] = useState({ type: '', text: '' });

  useEffect(() => {
    const 获取用户信息 = async () => {
      try {
        const res = await api.get('/users/me');
        set用户信息(res.data);
        set新昵称(res.data.username);
      } catch {
        set提示消息({ type: 'error', text: '获取用户信息失败' });
      } finally {
        set加载中(false);
      }
    };
    获取用户信息();
  }, []);

  const 显示提示 = (type, text) => {
    set提示消息({ type, text });
    setTimeout(() => set提示消息({ type: '', text: '' }), 3000);
  };

  const 处理修改昵称 = async () => {
    if (!新昵称.trim()) {
      显示提示('error', '昵称不能为空');
      return;
    }
    if (昵称提交中) return;
    set昵称提交中(true);
    try {
      const res = await api.put('/users/profile', { username: 新昵称.trim() });
      set用户信息(res.data);
      显示提示('success', '昵称修改成功');
      set昵称弹窗(false);
    } catch (err) {
      const msg = err.response?.data?.message || '修改失败';
      显示提示('error', msg);
    } finally {
      set昵称提交中(false);
    }
  };

  const 处理修改密码 = async () => {
    if (!旧密码 || !新密码 || !确认密码) {
      显示提示('error', '请填写完整信息');
      return;
    }
    if (新密码 !== 确认密码) {
      显示提示('error', '两次密码不一致');
      return;
    }
    if (新密码.length < 6) {
      显示提示('error', '新密码至少6位');
      return;
    }
    if (密码提交中) return;
    set密码提交中(true);
    try {
      await api.post('/users/change-password', { old_password: 旧密码, new_password: 新密码 });
      显示提示('success', '密码修改成功');
      set密码弹窗(false);
      set旧密码('');
      set新密码('');
      set确认密码('');
    } catch (err) {
      const msg = err.response?.data?.message || '修改失败';
      显示提示('error', msg);
    } finally {
      set密码提交中(false);
    }
  };

  const 处理退出登录 = () => {
    localStorage.clear();
    window.dispatchEvent(new Event('auth-change'));
    navigate('/');
  };

  const 返回仪表盘 = () => {
    navigate(`/${role}`);
  };

  if (加载中) {
    return (
      <div className="account-container">
        <div className="loading-spinner">加载中...</div>
      </div>
    );
  }

  const 用户 = 用户信息;

  return (
    <div className="account-container">
      <header className="account-header">
        <div className="header-left">
          <button className="back-btn" onClick={返回仪表盘}>← 返回</button>
          <h1>账户管理</h1>
        </div>
        <div className="header-right">
          <button className="logout-btn" onClick={处理退出登录}>退出登录</button>
        </div>
      </header>

      {提示消息.text && (
        <div className={`toast toast-${提示消息.type}`}>{提示消息.text}</div>
      )}

      <main className="account-content">
        <div className="profile-card">
          <div className="avatar-section">
            <div className="avatar">
              {用户.username.charAt(0).toUpperCase()}
            </div>
            <div className="user-basic">
              <h2>{用户.username}</h2>
              <p className="email">{用户.email}</p>
              {用户.phone && <p className="phone">{用户.phone}</p>}
              <span className={`role-badge role-${用户.role}`}>
                {用户.role === 'user' ? '玩家' : 用户.role === 'handler' ? '打手' : '管理员'}
              </span>
            </div>
          </div>
        </div>

        <div className="account-sections">
          <div className="section-card">
            <h3 className="section-title">基本资料</h3>
            <div className="info-row">
              <span className="info-label">昵称</span>
              <div className="info-value">
                <span>{用户.username}</span>
                <button className="edit-btn" onClick={() => set昵称弹窗(true)}>修改</button>
              </div>
            </div>
            <div className="info-row">
              <span className="info-label">邮箱</span>
              <span className="info-value">{用户.email}</span>
            </div>
            {用户.phone && (
              <div className="info-row">
                <span className="info-label">手机号</span>
                <span className="info-value">{用户.phone}</span>
              </div>
            )}
          </div>

          {用户.role === 'handler' && (
            <div className="section-card">
              <h3 className="section-title">打手信息</h3>
              <div className="info-row">
                <span className="info-label">打手等级</span>
                <span className="info-value">
                  <span className="level-stars">{'⭐'.repeat(用户.level || 1)}</span>
                  <span className="level-number">Lv.{用户.level || 1}</span>
                </span>
              </div>
              <div className="info-row">
                <span className="info-label">完成率</span>
                <span className="info-value">{用户.completion_rate || 0}%</span>
              </div>
              <div className="info-row">
                <span className="info-label">总订单数</span>
                <span className="info-value">{用户.total_orders || 0}</span>
              </div>
              <div className="info-row">
                <span className="info-label">余额</span>
                <span className="info-value">{用户.balance || 0} 元</span>
              </div>
            </div>
          )}

          {用户.role === 'user' && 用户.balance !== undefined && (
            <div className="section-card">
              <h3 className="section-title">账户信息</h3>
              <div className="info-row">
                <span className="info-label">余额</span>
                <span className="info-value">{用户.balance || 0} 元</span>
              </div>
            </div>
          )}

          <div className="section-card">
            <h3 className="section-title">安全设置</h3>
            <div className="info-row">
              <span className="info-label">登录密码</span>
              <div className="info-value">
                <span>••••••••</span>
                <button className="edit-btn" onClick={() => set密码弹窗(true)}>修改</button>
              </div>
            </div>
          </div>
        </div>
      </main>

      {昵称弹窗 && (
        <div className="modal-overlay" onClick={() => set昵称弹窗(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3 className="modal-title">修改昵称</h3>
            <input
              className="modal-input"
              value={新昵称}
              onChange={e => set新昵称(e.target.value)}
              placeholder="请输入新昵称"
            />
            <div className="modal-actions">
              <button className="modal-btn cancel" onClick={() => set昵称弹窗(false)}>取消</button>
              <button
                className={`modal-btn confirm ${昵称提交中 ? 'loading' : ''}`}
                onClick={处理修改昵称}
                disabled={昵称提交中}
              >
                {昵称提交中 ? '提交中...' : '确定'}
              </button>
            </div>
          </div>
        </div>
      )}

      {密码弹窗 && (
        <div className="modal-overlay" onClick={() => set密码弹窗(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3 className="modal-title">修改密码</h3>
            <input
              className="modal-input"
              type="password"
              value={旧密码}
              onChange={e => set旧密码(e.target.value)}
              placeholder="请输入旧密码"
            />
            <input
              className="modal-input"
              type="password"
              value={新密码}
              onChange={e => set新密码(e.target.value)}
              placeholder="请输入新密码（至少6位）"
            />
            <input
              className="modal-input"
              type="password"
              value={确认密码}
              onChange={e => set确认密码(e.target.value)}
              placeholder="请确认新密码"
            />
            <div className="modal-actions">
              <button className="modal-btn cancel" onClick={() => set密码弹窗(false)}>取消</button>
              <button
                className={`modal-btn confirm ${密码提交中 ? 'loading' : ''}`}
                onClick={处理修改密码}
                disabled={密码提交中}
              >
                {密码提交中 ? '提交中...' : '确定'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AccountSettings;
