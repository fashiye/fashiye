import React, { useState, useEffect, useCallback, useRef } from 'react';
import api from '../utils/api';
import 样式 from './ChatPanel.module.css';

const ChatPanel = ({ orderId, handlerId, userId }) => {
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [hasConversation, setHasConversation] = useState(false);
  const messagesEndRef = useRef(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const 最新消息ID = useRef(0); // 记录最新消息ID，用于增量轮询

  // 从 localStorage 获取当前用户信息
  const 当前角色 = localStorage.getItem('role') || 'user';
  const 当前用户ID = parseInt(localStorage.getItem('userId') || '0');

  // 根据当前角色确定"对方"是谁
  // 当前是用户 → 对方是打手（handlerId）；当前是打手 → 对方是用户（userId）
  const 对方ID = 当前角色 === 'user' ? handlerId : userId;
  const 对方类型 = 当前角色 === 'user' ? 'handler' : 'user';
  const 对方显示名 = 当前角色 === 'user' ? '打手' : '用户';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchConversationAndMessages = useCallback(async () => {
    if (!orderId || !对方ID) return;

    setIsLoading(true);
    try {
      // 调用库函数：获取会话列表
      // 传入：无参数（GET 请求）
      // 作用：从后端获取当前用户的所有会话
      // 传出：包含会话列表的响应，每个会话含 otherPartyId、otherPartyRole 等字段
      const response = await api.get('/conversations');
      // 用后端统一返回的 otherPartyId + otherPartyRole 查找匹配的会话
      let conv = response.data.data.find(c =>
        c.otherPartyId === 对方ID &&
        c.otherPartyRole === 对方类型
      );

      if (!conv) {
        // 调用库函数：创建新会话
        // 传入：otherPartyType(对方角色), otherPartyId(对方ID), type(会话类型), orderId(订单ID)
        // 作用：在服务端创建一条新的聊天会话
        // 传出：包含新会话ID的响应
        const createResponse = await api.post('/conversations', {
          otherPartyType: 对方类型,
          otherPartyId: 对方ID,
          type: 'user_handler',
          orderId: orderId
        });
        conv = { id: createResponse.data.data.id };
      }

      if (conv && conv.id) {
        setConversationId(conv.id);
        setHasConversation(true);

        // 调用库函数：获取消息列表
        // 传入：会话ID（路径参数）
        // 作用：获取指定会话的所有消息记录
        // 传出：消息对象数组
        const messagesResponse = await api.get(`/conversations/${conv.id}/messages`);
        setMessages(messagesResponse.data.data);

        if (messagesResponse.data.data.length > 0) {
          const lastMsgId = messagesResponse.data.data[messagesResponse.data.data.length - 1].id;
          最新消息ID.current = lastMsgId;
          // 调用库函数：标记已读
          // 传入：last_read_message_id(最后一条已读消息ID)
          // 作用：将指定消息之前的所有消息标记为已读
          // 传出：无返回值
          await api.post(`/conversations/${conv.id}/read`, { last_read_message_id: lastMsgId });
        }
      }
    } catch (err) {
      console.error('获取会话失败:', err);
    } finally {
      setIsLoading(false);
    }
  }, [orderId, 对方ID, 对方类型]);

  useEffect(() => {
    fetchConversationAndMessages();
  }, [fetchConversationAndMessages]);

  useEffect(() => {
    if (autoScroll) {
      scrollToBottom();
    }
  }, [messages, autoScroll]);

  // 轮询：每 3 秒拉取新消息，实现实时更新
  // 只在有会话ID时工作
  useEffect(() => {
    if (!conversationId) return;

    // 轮询回调：拉取最新消息列表，追加不重复的新消息
    const 轮询新消息 = async () => {
      try {
        // 调用库函数：获取消息列表
        // 传入：conversationId(会话ID)
        // 作用：获取指定会话的最新消息记录（限制20条）
        // 传出：消息对象数组
        const response = await api.get(`/conversations/${conversationId}/messages`, {
          params: { limit: 20 }
        });
        const 新消息列表 = response.data.data;

        if (新消息列表 && 新消息列表.length > 0) {
          // 只追加不在当前列表中的消息（按 ID 去重）
          setMessages(prev => {
            const 现有ID集合 = new Set(prev.map(m => m.id));
            const 真正新消息 = 新消息列表.filter(m => !现有ID集合.has(m.id));
            if (真正新消息.length === 0) return prev;
            最新消息ID.current = 真正新消息[真正新消息.length - 1].id;
            return [...prev, ...真正新消息];
          });
        }
      } catch {
        // 轮询失败静默忽略，下次继续
      }
    };

    // 每 3 秒执行一次轮询
    const 轮询定时器 = setInterval(轮询新消息, 3000);

    // 组件卸载或 conversationId 变化时清除定时器
    return () => clearInterval(轮询定时器);
  }, [conversationId]);

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

      // 本地构造消息对象，后端只返回 messageId
      const messageId = response.data.data.messageId;
      const 新消息 = {
        id: messageId,
        senderId: 当前用户ID,
        senderType: 当前角色,
        content: newMessage,
        contentType: 'text',
        createdAt: new Date().toISOString()
      };
      最新消息ID.current = messageId;
      setMessages(prev => [...prev, 新消息]);
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

  // 格式化时间，显示年月日时分
  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    const 时间对象 = new Date(timeStr);
    return 时间对象.toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit'
    });
  };

  // 根据发送者类型获取显示名称
  const getSenderName = (senderType) => {
    if (senderType === 'handler') return '打手';
    if (senderType === 'user') return '用户';
    return senderType;
  };

  // 无打手接单时显示占位
  if (!handlerId) {
    return (
      <div className={样式.chatPanel}>
        <div className={样式.chatHeader}>
          <h3>聊天</h3>
        </div>
        <div className={样式.chatMessages}>
          <div className={样式.noHandlerMessage}>
            订单尚未被接单，暂无聊天对象
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className={样式.chatPanel}>
        <div className={样式.chatHeader}>
          <h3>聊天</h3>
        </div>
        <div className={样式.chatMessages}>
          <div className={样式.loadingMessage}>加载中...</div>
        </div>
      </div>
    );
  }

  return (
    <div className={样式.chatPanel}>
      <div className={样式.chatHeader}>
        <h3>聊天</h3>
      </div>

      <div
        className={样式.chatMessages}
        onScroll={handleScroll}
      >
        {messages.length === 0 ? (
          <div className={样式.noMessages}>
            暂无消息，开始与{对方显示名}沟通吧！
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`${样式.message} ${msg.senderType === 当前角色 ? 样式.sent : 样式.received}`}
            >
              <div className={样式.messageSender}>{getSenderName(msg.senderType)}</div>
              <div className={样式.messageContent}>
                {msg.content}
              </div>
              <div className={样式.messageTime}>
                {formatTime(msg.createdAt)}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSendMessage} className={样式.chatInputForm}>
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="输入消息..."
          className={样式.chatInput}
          disabled={!hasConversation}
        />
        <button
          type="submit"
          disabled={!newMessage.trim() || isSending || !hasConversation}
          className={样式.sendBtn}
        >
          发送
        </button>
      </form>
    </div>
  );
};

export default ChatPanel;
