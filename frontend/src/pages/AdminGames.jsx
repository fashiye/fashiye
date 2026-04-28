import React, { useState, useEffect, useCallback } from 'react';
import api from '../utils/api';
import './AdminGames.css';

const 游戏图标 = {
  王者荣耀: '',
  英雄联盟: '',
  和平精英: ''
};

const 状态管理 = () => {
  const [游戏列表, 设置游戏列表] = useState([]);
  const [项目映射, 设置项目映射] = useState({});
  const [展开的游戏ID, 设置展开的游戏ID] = useState(null);
  const [加载中, 设置加载中] = useState(true);
  const [显示新建游戏弹窗, 设置显示新建游戏弹窗] = useState(false);
  const [显示新建项目弹窗, 设置显示新建项目弹窗] = useState(false);
  const [显示编辑游戏弹窗, 设置显示编辑游戏弹窗] = useState(false);
  const [选中的游戏, 设置选中的游戏] = useState(null);
  const [编辑中的游戏, 设置编辑中的游戏] = useState(null);
  const [提示信息, 设置提示信息] = useState(null);

  const 显示提示 = (消息, 类型 = 'success') => {
    设置提示信息({ 消息, 类型 });
    setTimeout(() => 设置提示信息(null), 3000);
  };

  const 获取游戏列表 = useCallback(async () => {
    try {
      const 响应 = await api.get('/games');
      设置游戏列表(响应.data);
      响应.data.forEach(游戏 => 获取项目列表(游戏.id));
    } catch (错误) {
      console.error('获取游戏列表失败:', 错误);
      显示提示('获取游戏列表失败', 'error');
    } finally {
      设置加载中(false);
    }
  }, []);

  const 获取项目列表 = async (游戏ID) => {
    try {
      const 响应 = await api.get(`/games/${游戏ID}/projects`);
      设置项目映射(prev => ({ ...prev, [游戏ID]: 响应.data }));
    } catch (错误) {
      console.error('获取项目列表失败:', 错误);
    }
  };

  useEffect(() => {
    获取游戏列表();
  }, [获取游戏列表]);

  const 切换展开 = (游戏ID) => {
    设置展开的游戏ID(展开的游戏ID === 游戏ID ? null : 游戏ID);
  };

  const 处理创建游戏 = async (事件) => {
    事件.preventDefault();
    const 表单数据 = new FormData(事件.target);
    try {
      await api.post('/games', {
        name: 表单数据.get('name'),
        description: 表单数据.get('description'),
        icon: 表单数据.get('icon') || ''
      });
      显示提示('游戏创建成功！');
      设置显示新建游戏弹窗(false);
      获取游戏列表();
    } catch (错误) {
      显示提示('创建游戏失败', 'error');
    }
  };

  const 处理编辑游戏 = async (事件) => {
    事件.preventDefault();
    const 表单数据 = new FormData(事件.target);
    try {
      await api.put(`/games/${编辑中的游戏.id}`, {
        name: 表单数据.get('name'),
        description: 表单数据.get('description'),
        icon: 表单数据.get('icon') || ''
      });
      显示提示('游戏更新成功！');
      设置显示编辑游戏弹窗(false);
      获取游戏列表();
    } catch (错误) {
      显示提示('更新游戏失败', 'error');
    }
  };

  const 处理删除游戏 = async (游戏ID, 游戏名称) => {
    if (!window.confirm(`确定要删除游戏「${游戏名称}」及其所有项目？此操作不可恢复！`)) return;
    try {
      await api.delete(`/games/${游戏ID}`);
      显示提示(`游戏「${游戏名称}」已删除`);
      获取游戏列表();
    } catch (错误) {
      显示提示('删除游戏失败', 'error');
    }
  };

  const 处理创建项目 = async (事件) => {
    事件.preventDefault();
    const 表单数据 = new FormData(事件.target);
    try {
      await api.post(`/games/${选中的游戏.id}/projects`, {
        name: 表单数据.get('name'),
        description: 表单数据.get('description'),
        price: parseFloat(表单数据.get('price')),
        unit: 表单数据.get('unit'),
        icon: 表单数据.get('icon') || '',
        is_single_per_order: 表单数据.get('is_single_per_order') === 'on'
      });
      显示提示('项目创建成功！');
      设置显示新建项目弹窗(false);
      获取项目列表(选中的游戏.id);
    } catch (错误) {
      显示提示('创建项目失败', 'error');
    }
  };

  const 处理删除项目 = async (游戏ID, 项目ID, 项目名称) => {
    if (!window.confirm(`确定要删除项目「${项目名称}」？`)) return;
    try {
      await api.delete(`/games/${游戏ID}/projects/${项目ID}`);
      显示提示(`项目「${项目名称}」已删除`);
      获取项目列表(游戏ID);
    } catch (错误) {
      显示提示('删除项目失败', 'error');
    }
  };

  return (
    <div className="games-page">
      <header className="games-header">
        <div className="header-left">
          <button className="icon-btn" onClick={() => window.history.back()} title="返回">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>
          <div>
            <h1>游戏管理</h1>
            <p className="header-subtitle">管理游戏及其服务项目</p>
          </div>
        </div>
        <button className="primary-btn" onClick={() => 设置显示新建游戏弹窗(true)}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          添加游戏
        </button>
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
        ) : 游戏列表.length === 0 ? (
          <div className="empty-state">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
              <line x1="8" y1="21" x2="16" y2="21" />
              <line x1="12" y1="17" x2="12" y2="21" />
            </svg>
            <h3>暂无游戏</h3>
            <p>点击上方按钮添加第一个游戏</p>
          </div>
        ) : (
          <div className="games-grid">
            {游戏列表.map(游戏 => (
              <div key={游戏.id} className="game-card">
                <div className="game-card-header">
                  <div className="game-icon-wrap">
                    {游戏.icon ? (
                      <img src={游戏.icon} alt={游戏.name} className="game-icon" />
                    ) : (
                      <div className="game-icon-placeholder">
                        {游戏.name.charAt(0)}
                      </div>
                    )}
                  </div>
                  <div className="game-meta">
                    <h2 className="game-name">{游戏.name}</h2>
                    <span className="game-desc">{游戏.description || '暂无描述'}</span>
                  </div>
                  <div className="game-actions">
                    <button
                      className="icon-btn-sm"
                      onClick={() => {
                        设置编辑中的游戏(游戏);
                        设置显示编辑游戏弹窗(true);
                      }}
                      title="编辑游戏"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                      </svg>
                    </button>
                    <button
                      className="icon-btn-sm danger"
                      onClick={() => 处理删除游戏(游戏.id, 游戏.name)}
                      title="删除游戏"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      </svg>
                    </button>
                    <button
                      className={`expand-btn ${展开的游戏ID === 游戏.id ? 'expanded' : ''}`}
                      onClick={() => 切换展开(游戏.id)}
                      title="展开项目"
                    >
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="9 18 15 12 9 6" />
                      </svg>
                    </button>
                  </div>
                </div>

                <div className={`projects-section ${展开的游戏ID === 游戏.id ? 'open' : ''}`}>
                  {项目映射[游戏.id] && 项目映射[游戏.id].length > 0 ? (
                    <div className="projects-list">
                      {项目映射[游戏.id].map(项目 => (
                        <div key={项目.id} className="project-row">
                          <div className="project-info">
                            <span className="project-name">
                              {项目.name}
                              {项目.is_single_per_order && (
                                <span className="single-badge">每单限购</span>
                              )}
                            </span>
                            {项目.description && (
                              <span className="project-desc">{项目.description}</span>
                            )}
                          </div>
                          <div className="project-price">
                            <span className="price-value">¥{项目.price}</span>
                            <span className="price-unit">/{项目.unit || '次'}</span>
                          </div>
                          <button
                            className="icon-btn-xs danger"
                            onClick={() => 处理删除项目(游戏.id, 项目.id, 项目.name)}
                            title="删除项目"
                          >
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                              <line x1="18" y1="6" x2="6" y2="18" />
                              <line x1="6" y1="6" x2="18" y2="18" />
                            </svg>
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="no-projects">
                      <span>暂无项目</span>
                    </div>
                  )}
                  <button
                    className="add-project-btn"
                    onClick={() => {
                      设置选中的游戏(游戏);
                      设置显示新建项目弹窗(true);
                    }}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="12" y1="5" x2="12" y2="19" />
                      <line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                    添加项目
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* 新建游戏弹窗 */}
      {显示新建游戏弹窗 && (
        <div className="modal-overlay" onClick={() => 设置显示新建游戏弹窗(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>添加新游戏</h2>
              <button className="close-btn" onClick={() => 设置显示新建游戏弹窗(false)}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <form onSubmit={处理创建游戏} className="modal-form">
              <div className="form-group">
                <label>游戏名称</label>
                <input name="name" placeholder="例如：王者荣耀" required />
              </div>
              <div className="form-group">
                <label>游戏描述</label>
                <textarea name="description" placeholder="简要描述这个游戏" rows="3" />
              </div>
              <div className="form-group">
                <label>图标链接（可选）</label>
                <input name="icon" placeholder="输入图标 URL" />
              </div>
              <div className="modal-footer">
                <button type="button" className="cancel-btn" onClick={() => 设置显示新建游戏弹窗(false)}>取消</button>
                <button type="submit" className="primary-btn">确认创建</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 编辑游戏弹窗 */}
      {显示编辑游戏弹窗 && 编辑中的游戏 && (
        <div className="modal-overlay" onClick={() => 设置显示编辑游戏弹窗(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>编辑游戏</h2>
              <button className="close-btn" onClick={() => 设置显示编辑游戏弹窗(false)}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <form onSubmit={处理编辑游戏} className="modal-form">
              <div className="form-group">
                <label>游戏名称</label>
                <input name="name" defaultValue={编辑中的游戏.name} placeholder="例如：王者荣耀" required />
              </div>
              <div className="form-group">
                <label>游戏描述</label>
                <textarea name="description" defaultValue={编辑中的游戏.description} placeholder="简要描述这个游戏" rows="3" />
              </div>
              <div className="form-group">
                <label>图标链接（可选）</label>
                <input name="icon" defaultValue={编辑中的游戏.icon || ''} placeholder="输入图标 URL" />
              </div>
              <div className="modal-footer">
                <button type="button" className="cancel-btn" onClick={() => 设置显示编辑游戏弹窗(false)}>取消</button>
                <button type="submit" className="primary-btn">保存修改</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 新建项目弹窗 */}
      {显示新建项目弹窗 && 选中的游戏 && (
        <div className="modal-overlay" onClick={() => 设置显示新建项目弹窗(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>为「{选中的游戏.name}」添加项目</h2>
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

export default 状态管理;