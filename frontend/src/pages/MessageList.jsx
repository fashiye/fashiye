import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './MessageList.css';

const MessageList = () => {
  const navigate = useNavigate();
  const [conversations, setConversations] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/conversations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setConversations(response.data);
    } catch (err) {
      console.error('获取会话列表失败:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    const role = localStorage.getItem('role') || 'user';
    navigate(`/${role}`);
  };

  const handleSelectConversation = (conversationId) => {
    const role = localStorage.getItem('role') || 'user';
    navigate(`/${role}/messages/${conversationId}`);
  };

  const handleCreateConversation = () => {
    const role = localStorage.getItem('role') || 'user';
    navigate(`/${role}/messages/new`);
  };

  const getRoleText = (role) => {
    const roleMap = {
      'user': '玩家',
      'handler': '打手',
      'admin': '管理员'
    };
    return roleMap[role] || role;
  };

  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    const date = new Date(timeStr);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) {
      return '刚刚';
    } else if (diff < 3600000) {
      return `${Math.floor(diff / 60000)}分钟前`;
    } else if (diff < 86400000) {
      return `${Math.floor(diff / 3600000)}小时前`;
    } else if (diff < 604800000) {
      return `${Math.floor(diff / 86400000)}天前`;
    } else {
      return date.toLocaleDateString('zh-CN');
    }
  };

  return (
    <div className="message-list-container">
      <div className="message-list-content">
        <header className="message-list-header">
          <h1>消息中心</h1>
          <div className="header-actions">
            <button onClick={handleCreateConversation} className="create-btn">
              + 新建会话
            </button>
            <button onClick={handleBack} className="back-btn">返回</button>
          </div>
        </header>

        {isLoading ? (
          <div className="loading-state">加载中...</div>
        ) : conversations.length === 0 ? (
          <div className="empty-state">
            <p>暂无消息</p>
            <p>点击"新建会话"开始聊天</p>
          </div>
        ) : (
          <div className="conversations-list">
            {conversations.map(conv => (
              <div
                key={conv.id}
                className="conversation-card"
                onClick={() => handleSelectConversation(conv.id)}
              >
                <div className="conversation-avatar">
                  {conv.otherPartyAvatar ? (
                    <img src={conv.otherPartyAvatar} alt="头像" />
                  ) : (
                    <div className="default-avatar">
                      {conv.otherPartyUsername.charAt(0).toUpperCase()}
                    </div>
                  )}
                  {conv.unreadCount > 0 && (
                    <div className="unread-badge">{conv.unreadCount}</div>
                  )}
                </div>
                
                <div className="conversation-info">
                  <div className="conversation-header">
                    <h3 className="conversation-name">
                      {conv.otherPartyUsername}
                    </h3>
                    <span className="conversation-role">
                      {getRoleText(conv.otherPartyRole)}
                    </span>
                  </div>
                  
                  <p className="conversation-last-message">
                    {conv.lastMessage || '暂无消息'}
                  </p>
                  
                  <div className="conversation-footer">
                    <span className="conversation-time">
                      {formatTime(conv.lastMessageAt)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageList;
