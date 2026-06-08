import React, { useState, useEffect, useCallback, useRef } from 'react';
import api from '../utils/api';
import './ChatPanel.css';

const ChatPanel = ({ orderId, handlerId, userId }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [hasConversation, setHasConversation] = useState(false);
  const messagesEndRef = useRef(null);
  const [autoScroll, setAutoScroll] = useState(true);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchConversationAndMessages = useCallback(async () => {
    if (!orderId || !handlerId) return;
    
    setIsLoading(true);
    try {
      const response = await api.get('/conversations');
      let conv = response.data.find(c => 
        ((c.user_id === userId && c.handler_id === handlerId) || 
         (c.user_id === handlerId && c.handler_id === userId)) &&
        c.order_id === orderId
      );
      
      if (!conv && userId && handlerId) {
        const createResponse = await api.post('/conversations', { 
          otherPartyType: 'handler', 
          otherPartyId: handlerId, 
          type: 'user_handler',
          orderId: orderId
        });
        conv = createResponse.data;
      }
      
      if (conv) {
        setConversationId(conv.id);
        setHasConversation(true);
        
        const messagesResponse = await api.get(`/conversations/${conv.id}/messages`);
        setMessages(messagesResponse.data);
        
        if (messagesResponse.data.length > 0) {
          const lastMsgId = messagesResponse.data[messagesResponse.data.length - 1].id;
          await api.post(`/conversations/${conv.id}/read`, { last_read_message_id: lastMsgId });
        }
      }
    } catch (err) {
      console.error('获取会话失败:', err);
    } finally {
      setIsLoading(false);
    }
  }, [orderId, handlerId, userId]);

  useEffect(() => {
    fetchConversationAndMessages();
  }, [fetchConversationAndMessages]);

  useEffect(() => {
    if (autoScroll) {
      scrollToBottom();
    }
  }, [messages, autoScroll]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim() || isSending || !conversationId) {
      return;
    }

    setIsSending(true);
    try {
      const response = await api.post(`/conversations/${conversationId}/messages`, { 
        content: newMessage, 
        contentType: 'text' 
      });
      
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

  const handleScroll = (e) => {
    const { scrollTop, scrollHeight, clientHeight } = e.target;
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 100;
    setAutoScroll(isNearBottom);
  };

  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    const date = new Date(timeStr);
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
  };

  const currentUserId = parseInt(localStorage.getItem('userId') || '0');

  if (!handlerId) {
    return (
      <div className="chat-panel">
        <div className="chat-header">
          <h3>💬 聊天</h3>
        </div>
        <div className="chat-messages">
          <div className="no-handler-message">
            订单尚未被接单，暂无聊天对象
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="chat-panel">
        <div className="chat-header">
          <h3>💬 聊天</h3>
        </div>
        <div className="chat-messages">
          <div className="loading-message">加载中...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <h3>💬 与打手聊天</h3>
      </div>
      
      <div 
        className="chat-messages" 
        onScroll={handleScroll}
      >
        {messages.length === 0 ? (
          <div className="no-messages">
            暂无消息，开始与打手沟通吧！
          </div>
        ) : (
          messages.map((msg) => (
            <div 
              key={msg.id} 
              className={`message ${msg.sender_id === currentUserId ? 'sent' : 'received'}`}
            >
              <div className="message-content">
                {msg.content}
              </div>
              <div className="message-time">
                {formatTime(msg.created_at)}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={handleSendMessage} className="chat-input-form">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="输入消息..."
          className="chat-input"
          disabled={!hasConversation}
        />
        <button 
          type="submit" 
          disabled={!newMessage.trim() || isSending || !hasConversation}
          className="send-btn"
        >
          发送
        </button>
      </form>
    </div>
  );
};

export default ChatPanel;
