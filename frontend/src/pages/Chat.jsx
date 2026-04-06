import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import './Chat.css';

const Chat = () => {
  const navigate = useNavigate();
  const { conversationId } = useParams();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [conversation, setConversation] = useState(null);
  const [userRole, setUserRole] = useState('');
  const messagesEndRef = useRef(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [availableUsers, setAvailableUsers] = useState([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchMessages = useCallback(async () => {
    if (!/^\d+$/.test(conversationId)) return;
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/conversations/${conversationId}/messages`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setMessages(response.data);
    } catch (err) {
      console.error('获取消息失败:', err);
    } finally {
      setIsLoading(false);
    }
  }, [conversationId]);

  const fetchConversationInfo = useCallback(async () => {
    if (!/^\d+$/.test(conversationId)) return;
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/conversations`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const conv = response.data.find(c => c.id === parseInt(conversationId));
      if (conv) {
        setConversation(conv);
      }
    } catch (err) {
      console.error('获取会话信息失败:', err);
    }
  }, [conversationId]);

  useEffect(() => {
    setUserRole(localStorage.getItem('role') || 'user');
    if (/^\d+$/.test(conversationId)) {
      fetchMessages();
      fetchConversationInfo();
    } else {
      fetchAvailableUsers();
    }
  }, [conversationId, fetchMessages, fetchConversationInfo]);

  const fetchAvailableUsers = async () => {
    setIsLoadingUsers(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${import.meta.env.VITE_API_BASE_URL}/users/available`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAvailableUsers(response.data);
    } catch (err) {
      console.error('获取用户列表失败:', err);
    } finally {
      setIsLoadingUsers(false);
    }
  };

  const handleCreateConversation = async (otherPartyType, otherPartyId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/conversations`,
        { otherPartyType, otherPartyId, type: 'user_handler' },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      const role = localStorage.getItem('role') || 'user';
      navigate(`/${role}/messages/${response.data.id}`);
    } catch (err) {
      console.error('创建会话失败:', err);
      alert(err.response?.data?.detail || '创建会话失败');
    }
  };

  useEffect(() => {
    if (autoScroll) {
      scrollToBottom();
    }
  }, [messages, autoScroll]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || isSending) {
      return;
    }

    setIsSending(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${import.meta.env.VITE_API_BASE_URL}/conversations/${conversationId}/messages`,
        { content: newMessage, contentType: 'text' },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setMessages(prev => [...prev, response.data]);
      setNewMessage('');
      setAutoScroll(true);
    } catch (err) {
      console.error('发送消息失败:', err);
      alert('发送消息失败，请重试');
    } finally {
      setIsSending(false);
    }
  };

  const handleBack = () => {
    const role = localStorage.getItem('role') || 'user';
    navigate(`/${role}/messages`);
  };

  const handleScroll = (e) => {
    const { scrollTop, scrollHeight, clientHeight } = e.target;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
    setAutoScroll(isNearBottom);
  };

  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    const date = new Date(timeStr);
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const getRoleText = (role) => {
    const roleMap = {
      'user': '玩家',
      'handler': '打手',
      'admin': '管理员'
    };
    return roleMap[role] || role;
  };

  if (!/^\d+$/.test(conversationId)) {
    return (
      <div className="chat-container">
        <header className="chat-header">
          <div className="chat-header-left">
            <button onClick={handleBack} className="back-btn">←</button>
            <h2 className="chat-header-name">新建会话</h2>
          </div>
        </header>
        <div className="chat-messages">
          {isLoadingUsers ? (
            <div className="loading-state">加载中...</div>
          ) : availableUsers.length === 0 ? (
            <div className="empty-state">
              <p>暂无可用用户</p>
            </div>
          ) : (
            <div className="conversations-list">
              {availableUsers.map(u => (
                <div
                  key={`${u.role}-${u.id}`}
                  className="conversation-card"
                  onClick={() => handleCreateConversation(u.role, u.id)}
                >
                  <div className="conversation-avatar">
                    <div className="default-avatar">
                      {u.username.charAt(0).toUpperCase()}
                    </div>
                  </div>
                  <div className="conversation-info">
                    <div className="conversation-header">
                      <h3 className="conversation-name">{u.username}</h3>
                      <span className="conversation-role">
                        {getRoleText(u.role)}
                      </span>
                    </div>
                    {u.orderInfo && (
                      <p className="conversation-last-message">
                        订单 {u.orderNo}：{u.orderInfo}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  if (!conversation) {
    return (
      <div className="chat-container">
        <div className="loading-state">加载中...</div>
      </div>
    );
  }

  return (
    <div className="chat-container">
      <header className="chat-header">
        <div className="chat-header-left">
          <button onClick={handleBack} className="back-btn">←</button>
          <div className="chat-header-info">
            <h2 className="chat-header-name">{conversation.otherPartyUsername}</h2>
            <span className="chat-header-role">
              {getRoleText(conversation.otherPartyRole)}
            </span>
          </div>
        </div>
      </header>

      <div className="chat-messages" onScroll={handleScroll}>
        {isLoading && messages.length === 0 ? (
          <div className="loading-state">加载中...</div>
        ) : messages.length === 0 ? (
          <div className="empty-state">
            <p>暂无消息</p>
            <p>开始聊天吧！</p>
          </div>
        ) : (
          <>
            {messages.map(msg => (
              <div
                key={msg.id}
                className={`message-item ${msg.senderType === userRole ? 'message-sent' : 'message-received'}`}
              >
                <div className="message-content">
                  <p className="message-text">{msg.content}</p>
                  <span className="message-time">{formatTime(msg.createdAt)}</span>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      <form onSubmit={handleSendMessage} className="chat-input-form">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="输入消息..."
          className="chat-input"
          disabled={isSending}
        />
        <button
          type="submit"
          className="send-btn"
          disabled={!newMessage.trim() || isSending}
        >
          {isSending ? '发送中...' : '发送'}
        </button>
      </form>
    </div>
  );
};

export default Chat;
