import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import api from '../utils/api';
import './AdminGames.css';

const AdminGameProjects = () => {
  const { gameId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const [游戏信息, 设置游戏信息] = useState(location.state?.游戏 || null);
  const [项目列表, 设置项目列表] = useState([]);
  const [加载中, 设置加载中] = useState(true);
  const [显示新建项目弹窗, 设置显示新建项目弹窗] = useState(false);
  const [提示信息, 设置提示信息] = useState(null);

  const 显示提示 = (消息, 类型 = 'success') => {
    设置提示信息({ 消息, 类型 });
    setTimeout(() => 设置提示信息(null), 3000);
  };

  // 如果没有通过 navigation state 传递游戏信息，则从列表获取
  const 获取游戏信息 = useCallback(async () => {
    if (游戏信息) return;
    try {
      const 响应 = await api.get('/games');
      const 游戏 = 响应.data.find(g => g.id === parseInt(gameId));
      if (游戏) {
        设置游戏信息(游戏);
      }
    } catch (错误) {
      console.error('获取游戏信息失败:', 错误);
    }
  }, [gameId, 游戏信息]);

  const 获取项目列表 = useCallback(async () => {
    try {
      const 响应 = await api.get(`/games/${gameId}/projects`);
      设置项目列表(响应.data);
    } catch (错误) {
      console.error('获取项目列表失败:', 错误);
      显示提示('获取项目列表失败', 'error');
    } finally {
      设置加载中(false);
    }
  }, [gameId]);

  useEffect(() => {
    获取游戏信息();
    获取项目列表();
  }, [获取游戏信息, 获取项目列表]);

  const 处理创建项目 = async (事件) => {
    事件.preventDefault();
    const 表单数据 = new FormData(事件.target);
    try {
      await api.post(`/games/${gameId}/projects`, {
        name: 表单数据.get('name'),
        description: 表单数据.get('description'),
        price: parseFloat(表单数据.get('price')),
        unit: 表单数据.get('unit'),
        icon: 表单数据.get('icon') || '',
        is_single_per_order: 表单数据.get('is_single_per_order') === 'on'
      });
      显示提示('项目创建成功！');
      设置显示新建项目弹窗(false);
      获取项目列表();
    } catch (错误) {
      显示提示('创建项目失败', 'error');
    }
  };

  const 处理删除项目 = async (项目ID, 项目名称) => {
    if (!window.confirm(`确定要删除项目「${项目名称}」？`)) return;
    try {
      await api.delete(`/games/${gameId}/projects/${项目ID}`);
      显示提示(`项目「${项目名称}」已删除`);
      获取项目列表();
    } catch (错误) {
      显示提示('删除项目失败', 'error');
    }
  };

  return (
    <div className="games-page">
      <header className="games-header">
        <div className="header-left">
          <button className="icon-btn" onClick={() => navigate('/admin/games')} title="返回游戏列表">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>
          <div>
            <h1>{游戏信息?.name || '加载中...'}</h1>
            <p className="header-subtitle">
              {游戏信息?.description || '项目管理'} — 共 {项目列表.length} 个项目
            </p>
          </div>
        </div>
        <div className="header-right" style={{ display: 'flex', gap: '10px' }}>
          <button
            className="primary-btn"
            onClick={() => navigate('/admin/games')}
            style={{ background: 'rgba(255,255,255,0.2)', color: 'white', boxShadow: 'none' }}
          >
            返回游戏列表
          </button>
          <button className="primary-btn" onClick={() => 设置显示新建项目弹窗(true)}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            添加项目
          </button>
        </div>
      </header>

      <main className="games-main">
        {提示信息 && (
          <div className={`toast toast-${提示信息.类型}`}>
            <span>{提示信息.消息}</span>
          </div>
        )}

        {加载中 ? (
          <div className="loading-state">
            <div className="spinner" />
            <p>加载中...</p>
          </div>
        ) : 项目列表.length === 0 ? (
          <div className="empty-state">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
              <line x1="8" y1="21" x2="16" y2="21" />
              <line x1="12" y1="17" x2="12" y2="21" />
            </svg>
            <h3>暂无项目</h3>
            <p>点击上方「添加项目」按钮添加第一个服务项目</p>
          </div>
        ) : (
          <div style={{ background: 'white', borderRadius: '16px', boxShadow: '0 1px 4px rgba(0,0,0,0.06)', border: '1px solid #f0f0f5', overflow: 'hidden' }}>
            <div style={{
              padding: '16px 24px',
              borderBottom: '1px solid #f0f0f5',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              background: '#fafafa'
            }}>
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#555' }}>
                服务项目列表
              </span>
              <span style={{ fontSize: '13px', color: '#999' }}>
                共 {项目列表.length} 项
              </span>
            </div>
            <div style={{ padding: '16px 24px' }}>
              {项目列表.map(项目 => (
                <div
                  key={项目.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '14px 16px',
                    marginBottom: '8px',
                    background: '#f8f9fc',
                    borderRadius: '10px',
                    border: '1px solid #f0f0f5',
                    transition: 'all 0.2s'
                  }}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                      <span style={{ fontSize: '15px', fontWeight: 600, color: '#333' }}>
                        {项目.name}
                      </span>
                      {项目.is_single_per_order && (
                        <span style={{
                          display: 'inline-flex', alignItems: 'center',
                          fontSize: '11px', fontWeight: 600,
                          color: '#7c3aed', background: 'rgba(124,58,237,0.1)',
                          padding: '2px 8px', borderRadius: '10px',
                          whiteSpace: 'nowrap', lineHeight: '1.4'
                        }}>
                          每单限购
                        </span>
                      )}
                    </div>
                    {项目.description && (
                      <span style={{ fontSize: '13px', color: '#999' }}>
                        {项目.description}
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '2px', flexShrink: 0 }}>
                    <span style={{ fontSize: '16px', fontWeight: 700, color: '#ef4444' }}>¥{项目.price}</span>
                    <span style={{ fontSize: '12px', color: '#999' }}>/{项目.unit || '次'}</span>
                  </div>
                  <button
                    style={{
                      width: '28px', height: '28px', borderRadius: '6px',
                      border: '1px solid transparent', background: 'transparent',
                      color: '#999', display: 'flex', alignItems: 'center',
                      justifyContent: 'center', cursor: 'pointer', flexShrink: 0,
                      transition: 'all 0.2s'
                    }}
                    onClick={() => 处理删除项目(项目.id, 项目.name)}
                    title="删除项目"
                    onMouseOver={e => { e.currentTarget.style.background = '#fef2f2'; e.currentTarget.style.color = '#dc3545'; e.currentTarget.style.borderColor = '#fecaca'; }}
                    onMouseOut={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#999'; e.currentTarget.style.borderColor = 'transparent'; }}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* 新建项目弹窗 */}
      {显示新建项目弹窗 && (
        <div className="modal-overlay" onClick={() => 设置显示新建项目弹窗(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>为「{游戏信息?.name}」添加项目</h2>
              <button className="close-btn" onClick={() => 设置显示新建项目弹窗(false)}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <form onSubmit={处理创建项目} className="modal-form">
              <div className="form-group">
                <label>项目名称</label>
                <input name="name" placeholder="例如：排位上分" required />
              </div>
              <div className="form-group">
                <label>项目描述</label>
                <textarea name="description" placeholder="描述这个服务项目" rows="2" />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>价格</label>
                  <div className="input-with-suffix">
                    <input name="price" type="number" step="0.01" min="0" placeholder="0.00" required />
                    <span>¥</span>
                  </div>
                </div>
                <div className="form-group">
                  <label>单位</label>
                  <input name="unit" placeholder="例如：星、局、天" required />
                </div>
              </div>
              <div className="form-group">
                <label>图标链接（可选）</label>
                <input name="icon" placeholder="输入图标 URL" />
              </div>
              <div className="form-group checkbox-group">
                <label className="checkbox-label">
                  <input name="is_single_per_order" type="checkbox" />
                  <span className="checkbox-custom" />
                  <span>每单限购一个</span>
                </label>
                <p className="checkbox-hint">开启后，每个订单中此项目只能下单一个</p>
              </div>
              <div className="modal-footer">
                <button type="button" className="cancel-btn" onClick={() => 设置显示新建项目弹窗(false)}>取消</button>
                <button type="submit" className="primary-btn">确认添加</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminGameProjects;
