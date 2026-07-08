import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import 样式 from './AdminGames.module.css';  // 使用 CSS Modules 玻璃态样式

const 状态管理 = () => {
  const navigate = useNavigate();
  const [游戏列表, 设置游戏列表] = useState([]);
  const [加载中, 设置加载中] = useState(true);
  const [显示新建游戏弹窗, 设置显示新建游戏弹窗] = useState(false);
  const [显示编辑游戏弹窗, 设置显示编辑游戏弹窗] = useState(false);
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
    } catch (错误) {
      console.error('获取游戏列表失败:', 错误);
      显示提示('获取游戏列表失败', 'error');
    } finally {
      设置加载中(false);
    }
  }, []);

  useEffect(() => {
    获取游戏列表();
  }, [获取游戏列表]);

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

  const 跳转到项目管理 = (游戏) => {
    navigate(`/admin/games/${游戏.id}`, { state: { 游戏 } });
  };

  return (
    <div className={样式.gamesPage}>
      <header className={样式.gamesHeader}>
        <div className={样式.headerLeft}>
          <button className={样式.iconBtn} onClick={() => window.history.back()} title="返回">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>
          <div>
            <h1>游戏管理</h1>
            <p className={样式.headerSubtitle}>管理游戏及其服务项目</p>
          </div>
        </div>
        <button className={样式.primaryBtn} onClick={() => 设置显示新建游戏弹窗(true)}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          添加游戏
        </button>
      </header>

      <main className={样式.gamesMain}>
        {提示信息 && (
          <div className={`${样式.toast} ${提示信息.类型 === 'success' ? 样式.toastSuccess : 样式.toastError}`}>
            <span>{提示信息.消息}</span>
          </div>
        )}

        {加载中 ? (
          <div className={样式.loadingState}>
            <div className={样式.spinner} />
            <p>加载中...</p>
          </div>
        ) : 游戏列表.length === 0 ? (
          <div className={样式.emptyState}>
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
              <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
              <line x1="8" y1="21" x2="16" y2="21" />
              <line x1="12" y1="17" x2="12" y2="21" />
            </svg>
            <h3>暂无游戏</h3>
            <p>点击上方按钮添加第一个游戏</p>
          </div>
        ) : (
          <div className={样式.gamesGrid}>
            {游戏列表.map(游戏 => (
              <div key={游戏.id} className={样式.gameCard}>
                <div className={样式.gameCardHeader} style={{ cursor: 'pointer' }} onClick={() => 跳转到项目管理(游戏)}>
                  <div className={样式.gameIconWrap}>
                    {游戏.icon ? (
                      <img src={游戏.icon} alt={游戏.name} className={样式.gameIcon} />
                    ) : (
                      <div className={样式.gameIconPlaceholder}>
                        {游戏.name.charAt(0)}
                      </div>
                    )}
                  </div>
                  <div className={样式.gameMeta}>
                    <h2 className={样式.gameName}>{游戏.name}</h2>
                    <span className={样式.gameDesc}>{游戏.description || '暂无描述'}</span>
                  </div>
                  <div className={样式.gameActions} onClick={e => e.stopPropagation()}>
                    <button
                      className={样式.iconBtnSm}
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
                      className={样式.danger}
                      onClick={() => 处理删除游戏(游戏.id, 游戏.name)}
                      title="删除游戏"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      </svg>
                    </button>
                    <button
                      className={`${样式.expandBtn} ${样式.expanded}`}
                      onClick={() => 跳转到项目管理(游戏)}
                      title="管理项目"
                    >
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="9 18 15 12 9 6" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* 新建游戏弹窗 */}
      {显示新建游戏弹窗 && (
        <div className={样式.modalOverlay} onClick={() => 设置显示新建游戏弹窗(false)}>
          <div className={样式.modalContent} onClick={e => e.stopPropagation()}>
            <div className={样式.modalHeader}>
              <h2>添加新游戏</h2>
              <button className={样式.closeBtn} onClick={() => 设置显示新建游戏弹窗(false)}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <form onSubmit={处理创建游戏} className={样式.modalForm}>
              <div className={样式.formGroup}>
                <label>游戏名称</label>
                <input name="name" placeholder="例如：王者荣耀" required />
              </div>
              <div className={样式.formGroup}>
                <label>游戏描述</label>
                <textarea name="description" placeholder="简要描述这个游戏" rows="3" />
              </div>
              <div className={样式.formGroup}>
                <label>图标链接（可选）</label>
                <input name="icon" placeholder="输入图标 URL" />
              </div>
              <div className={样式.modalFooter}>
                <button type="button" className={样式.cancelBtn} onClick={() => 设置显示新建游戏弹窗(false)}>取消</button>
                <button type="submit" className={样式.primaryBtn}>确认创建</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 编辑游戏弹窗 */}
      {显示编辑游戏弹窗 && 编辑中的游戏 && (
        <div className={样式.modalOverlay} onClick={() => 设置显示编辑游戏弹窗(false)}>
          <div className={样式.modalContent} onClick={e => e.stopPropagation()}>
            <div className={样式.modalHeader}>
              <h2>编辑游戏</h2>
              <button className={样式.closeBtn} onClick={() => 设置显示编辑游戏弹窗(false)}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <form onSubmit={处理编辑游戏} className={样式.modalForm}>
              <div className={样式.formGroup}>
                <label>游戏名称</label>
                <input name="name" defaultValue={编辑中的游戏.name} placeholder="例如：王者荣耀" required />
              </div>
              <div className={样式.formGroup}>
                <label>游戏描述</label>
                <textarea name="description" defaultValue={编辑中的游戏.description} placeholder="简要描述这个游戏" rows="3" />
              </div>
              <div className={样式.formGroup}>
                <label>图标链接（可选）</label>
                <input name="icon" defaultValue={编辑中的游戏.icon || ''} placeholder="输入图标 URL" />
              </div>
              <div className={样式.modalFooter}>
                <button type="button" className={样式.cancelBtn} onClick={() => 设置显示编辑游戏弹窗(false)}>取消</button>
                <button type="submit" className={样式.primaryBtn}>保存修改</button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};

export default 状态管理;