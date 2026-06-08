import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import './OrderLookup.css';

const OrderLookup = () => {
  const navigate = useNavigate();
  const [orderNo, setOrderNo] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!orderNo.trim()) {
      setError('请输入凭据号');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await api.get(`/orders/lookup/${orderNo.trim()}`);
      
      if (response.data && response.data.data) {
        navigate(`/order-detail/${response.data.data.id}`);
      }
    } catch (err) {
      setError(err.response?.data?.detail || '查询失败，请检查凭据号是否正确');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="lookup-container">
      <div className="lookup-card">
        <div className="logo-icon">🔍</div>
        <h1 className="title">订单查询</h1>
        <p className="subtitle">输入您的凭据号查询订单状态</p>
        
        <form onSubmit={handleSearch}>
          <div className="input-group">
            <input
              type="text"
              value={orderNo}
              onChange={(e) => setOrderNo(e.target.value)}
              className="lookup-input"
              placeholder="请输入凭据号（如 BO2024010100001）"
              maxLength={50}
            />
          </div>
          
          {error && <div className="error-message">{error}</div>}
          
          <button
            type="submit"
            disabled={isLoading}
            className="search-btn"
          >
            {isLoading ? '查询中...' : '查询订单'}
          </button>
        </form>
        
        <div className="tips">
          <p className="tip-text">
            💡 提示：凭据号是您下单成功后获得的订单编号
          </p>
        </div>
        
        <div className="links">
          <a href="/game-order" className="link-btn">
            返回下单页面
          </a>
        </div>
      </div>
    </div>
  );
};

export default OrderLookup;
