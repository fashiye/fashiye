import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './OrderPool.css';

const OrderPool = () => {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [games, setGames] = useState([]);
  const [selectedGame, setSelectedGame] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [page, setPage] = useState(1);

  const fetchGames = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/games`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setGames(response.data);
    } catch (err) {
      console.error('获取游戏列表失败:', err);
    }
  }, []);

  const fetchOrders = useCallback(async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = { page, size: 20 };
      if (selectedGame) {
        params.game_id = selectedGame;
      }

      const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/orders/pool`, {
        headers: { Authorization: `Bearer ${token}` },
        params
      });

      setOrders(response.data);
    } catch (err) {
      console.error('获取订单池失败:', err);
    } finally {
      setIsLoading(false);
    }
  }, [page, selectedGame]);

  useEffect(() => {
    fetchGames();
    fetchOrders();
  }, [fetchGames, fetchOrders]);

  const handleAcceptOrder = async (orderId) => {
    if (!confirm('确定要接取这个订单吗？')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.post(`${import.meta.env.VITE_API_BASE_URL}/orders/${orderId}/accept`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });

      alert('接单成功！');
      fetchOrders();
    } catch (err) {
      alert('接单失败：' + (err.response?.data?.detail || err.message));
      console.error('Accept order error:', err);
    }
  };

  const handleBack = () => {
    navigate('/handler');
  };

  return (
    <div className="order-pool-container">
      <div className="order-pool-content">
        <header className="order-pool-header">
          <h1>订单池</h1>
          <button onClick={handleBack} className="back-btn">返回</button>
        </header>

        <div className="filter-section">
          <div className="filter-group">
            <label>筛选游戏：</label>
            <select
              value={selectedGame}
              onChange={(e) => {
                setSelectedGame(e.target.value);
                setPage(1);
              }}
            >
              <option value="">全部游戏</option>
              {games.map(game => (
                <option key={game.id} value={game.id}>{game.name}</option>
              ))}
            </select>
          </div>
        </div>

        {isLoading && orders.length === 0 ? (
          <div className="loading-state">加载中...</div>
        ) : orders.length === 0 ? (
          <div className="empty-state">
            <p>暂无可接订单</p>
            <p>请稍后再来查看</p>
          </div>
        ) : (
          <div className="orders-list">
            {orders.map(order => (
              <div key={order.id} className="order-card">
                <div className="order-header">
                  <h3>{order.gameName}</h3>
                  <span className="order-no">订单号：{order.orderNo}</span>
                </div>
                
                <div className="order-body">
                  <div className="order-info">
                    <span className="info-label">项目：</span>
                    <span className="info-value item-summary">{order.itemSummary}</span>
                  </div>
                  
                  <div className="order-info">
                    <span className="info-label">金额：</span>
                    <span className="info-value price">¥{order.totalAmount}</span>
                  </div>
                  
                  {order.requirements && (
                    <div className="order-info">
                      <span className="info-label">要求：</span>
                      <span className="info-value">{order.requirements}</span>
                    </div>
                  )}
                  
                  <div className="order-info">
                    <span className="info-label">发布时间：</span>
                    <span className="info-value">
                      {new Date(order.createdAt).toLocaleString('zh-CN')}
                    </span>
                  </div>
                </div>
                
                <div className="order-actions">
                  <button
                    onClick={() => handleAcceptOrder(order.id)}
                    className="accept-btn"
                  >
                    接单
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="pagination">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1 || isLoading}
            className="page-btn"
          >
            上一页
          </button>
          <span className="page-info">第 {page} 页</span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={orders.length < 20 || isLoading}
            className="page-btn"
          >
            下一页
          </button>
        </div>
      </div>
    </div>
  );
};

export default OrderPool;
