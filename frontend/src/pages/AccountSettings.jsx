import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import styles from './AccountSettings.module.css';

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
        set用户信息(res.data.data);
        set新昵称(res.data.data.username);
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
        await api.put('/users/profile', { username: 新昵称.trim() });
        // 调用库函数：重新获取用户信息
        // 传入：无参数
        // 作用：从后端重新拉取最新用户数据，确保界面同步
        // 传出：包含用户信息的响应对象
        const 重新获取 = await api.get('/users/me');
        set用户信息(重新获取.data.data);
        set新昵称(重新获取.data.data.username);
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
      <div className={styles.accountContainer}>
        <div className={styles.loadingSpinner}>加载中...</div>
      </div>
    );
  }

  const 用户 = 用户信息;

  if (!用户) {
    return (
      <div className={styles.accountContainer}>
        <div className={styles.loadingSpinner}>用户信息加载中...</div>
      </div>
    );
  }

  return (
    <div className={styles.accountContainer}>
      <header className={styles.accountHeader}>
        <div className={styles.headerLeft}>
          <button className={styles.backBtn} onClick={返回仪表盘}>← 返回</button>
          <h1>账户管理</h1>
        </div>
        <div className={styles.headerRight}>
          <button className={styles.logoutBtn} onClick={处理退出登录}>退出登录</button>
        </div>
      </header>

      {提示消息.text && (
        <div className={`${styles.toast} ${提示消息.type === 'success' ? styles.toastSuccess : styles.toastError}`}>{提示消息.text}</div>
      )}

      <main className={styles.accountContent}>
        <div className={styles.profileCard}>
          <div className={styles.avatarSection}>
            <div className={styles.avatar}>
              {用户?.username?.charAt(0)?.toUpperCase() || '?'}
            </div>
            <div className={styles.userBasic}>
              <h2>{用户.username}</h2>
              <p className={styles.email}>{用户.email}</p>
              {用户.phone && <p className={styles.phone}>{用户.phone}</p>}
              <span className={`${styles.roleBadge} ${用户.role === 'user' ? styles.roleUser : styles.roleHandler}`}>
                {用户.role === 'user' ? '玩家' : 用户.role === 'handler' ? '打手' : '管理员'}
              </span>
            </div>
          </div>
        </div>

        <div className={styles.accountSections}>
          <div className={styles.sectionCard}>
            <h3 className={styles.sectionTitle}>基本资料</h3>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>昵称</span>
              <div className={styles.infoValue}>
                <span>{用户.username}</span>
                <button className={styles.editBtn} onClick={() => set昵称弹窗(true)}>修改</button>
              </div>
            </div>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>邮箱</span>
              <span className={styles.infoValue}>{用户.email}</span>
            </div>
            {用户.phone && (
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>手机号</span>
                <span className={styles.infoValue}>{用户.phone}</span>
              </div>
            )}
          </div>

          {用户.role === 'handler' && (
            <div className={styles.sectionCard}>
              <h3 className={styles.sectionTitle}>打手信息</h3>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>打手等级</span>
                <span className={styles.infoValue}>
                  <span className={styles.levelStars}>{'⭐'.repeat(用户.level || 1)}</span>
                  <span className={styles.levelNumber}>Lv.{用户.level || 1}</span>
                </span>
              </div>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>完成率</span>
                <span className={styles.infoValue}>{用户.completion_rate || 0}%</span>
              </div>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>总订单数</span>
                <span className={styles.infoValue}>{用户.total_orders || 0}</span>
              </div>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>累计收入</span>
                <span className={styles.infoValue}>{用户.balance || 0} 元</span>
              </div>
            </div>
          )}

          {用户.role === 'user' && 用户.balance !== undefined && (
            <div className={styles.sectionCard}>
              <h3 className={styles.sectionTitle}>账户信息</h3>
              <div className={styles.infoRow}>
                <span className={styles.infoLabel}>余额</span>
                <span className={styles.infoValue}>{用户.balance || 0} 元</span>
              </div>
            </div>
          )}

          <div className={styles.sectionCard}>
            <h3 className={styles.sectionTitle}>安全设置</h3>
            <div className={styles.infoRow}>
              <span className={styles.infoLabel}>登录密码</span>
              <div className={styles.infoValue}>
                <span>••••••••</span>
                <button className={styles.editBtn} onClick={() => set密码弹窗(true)}>修改</button>
              </div>
            </div>
          </div>
        </div>
      </main>

      {昵称弹窗 && (
        <div className={styles.modalOverlay} onClick={() => set昵称弹窗(false)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <h3 className={styles.modalTitle}>修改昵称</h3>
            <input
              className={styles.modalInput}
              value={新昵称}
              onChange={e => set新昵称(e.target.value)}
              placeholder="请输入新昵称"
            />
            <div className={styles.modalActions}>
              <button className={`${styles.modalBtn} ${styles.cancel}`} onClick={() => set昵称弹窗(false)}>取消</button>
              <button
                className={`${styles.modalBtn} ${styles.confirm} ${昵称提交中 ? styles.loading : ''}`}
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
        <div className={styles.modalOverlay} onClick={() => set密码弹窗(false)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <h3 className={styles.modalTitle}>修改密码</h3>
            <input
              className={styles.modalInput}
              type="password"
              value={旧密码}
              onChange={e => set旧密码(e.target.value)}
              placeholder="请输入旧密码"
            />
            <input
              className={styles.modalInput}
              type="password"
              value={新密码}
              onChange={e => set新密码(e.target.value)}
              placeholder="请输入新密码（至少6位）"
            />
            <input
              className={styles.modalInput}
              type="password"
              value={确认密码}
              onChange={e => set确认密码(e.target.value)}
              placeholder="请确认新密码"
            />
            <div className={styles.modalActions}>
              <button className={`${styles.modalBtn} ${styles.cancel}`} onClick={() => set密码弹窗(false)}>取消</button>
              <button
                className={`${styles.modalBtn} ${styles.confirm} ${密码提交中 ? styles.loading : ''}`}
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
