import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './CreateOrder.css';

const CreateOrder = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    gameId: '',
    accountInfo: '',
    requirements: ''
  });
  const [items, setItems] = useState([
    { projectId: '', quantity: 1, unitPrice: 0 }
  ]);
  const [games, setGames] = useState([]);
  const [projects, setProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchGames = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/games`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setGames(response.data);
      if (response.data.length > 0) {
        setFormData(prev => ({ ...prev, gameId: response.data[0].id }));
        fetchProjects(response.data[0].id);
      }
    } catch (err) {
      console.error('获取游戏列表失败:', err);
    }
  }, []);

  const fetchProjects = async (gameId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/games/${gameId}/projects`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProjects(response.data);
    } catch (err) {
      console.error('获取项目列表失败:', err);
    }
  };

  useEffect(() => {
    fetchGames();
  }, [fetchGames]);

  const handleGameChange = (e) => {
    const gameId = e.target.value;
    setFormData(prev => ({ ...prev, gameId }));
    fetchProjects(gameId);
    // 清空已选择的项目
    setItems([{ projectId: '', quantity: 1, unitPrice: 0 }]);
  };

  const handleAddItem = () => {
    setItems(prev => [...prev, { projectId: '', quantity: 1, unitPrice: 0 }]);
  };

  const handleRemoveItem = (index) => {
    if (items.length <= 1) {
      setError('至少需要保留一个项目');
      return;
    }
    setItems(prev => prev.filter((_, i) => i !== index));
    setError('');
  };

  const handleItemChange = (index, field, value) => {
    setItems(prev => {
      const newItems = [...prev];
      newItems[index] = { ...newItems[index], [field]: value };
      
      // 如果修改了项目，更新单价
      if (field === 'projectId') {
        const project = projects.find(p => p.id === parseInt(value));
        newItems[index].unitPrice = project ? project.price : 0;
      }
      
      return newItems;
    });
  };

  const calculateTotal = () => {
    return items.reduce((total, item) => {
      return total + (item.unitPrice * item.quantity);
    }, 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    // 验证至少有一个有效的项目
    const validItems = items.filter(item => item.projectId && item.quantity >= 1);
    if (validItems.length === 0) {
      setError('请至少选择一个项目');
      return;
    }
    
    setIsLoading(true);

    try {
      const token = localStorage.getItem('token');
      const orderData = {
        gameId: parseInt(formData.gameId),
        accountInfo: formData.accountInfo,
        requirements: formData.requirements,
        items: validItems.map(item => ({
          projectId: parseInt(item.projectId),
          quantity: parseInt(item.quantity)
        }))
      };

      await axios.post(`${import.meta.env.VITE_API_BASE_URL}/orders`, orderData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      navigate('/user/orders');
    } catch (err) {
      setError('发布订单失败，请检查输入信息');
      console.error('Create order error:', err);
      if (err.response) {
        console.error('Response data:', err.response.data);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/user');
  };

  return (
    <div className="create-order-container">
      <div className="create-order-card">
        <header className="create-order-header">
          <h1>发布订单</h1>
          <button onClick={handleBack} className="back-btn">返回</button>
        </header>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit} className="create-order-form">
          <div className="form-section">
            <h2>基本信息</h2>
            
            <div className="form-group">
              <label>选择游戏 *</label>
              <select
                value={formData.gameId}
                onChange={handleGameChange}
                required
                disabled={isLoading}
              >
                <option value="">请选择游戏</option>
                {games.map(game => (
                  <option key={game.id} value={game.id}>{game.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-section">
            <h2>项目列表 *</h2>
            
            <div className="items-list">
              <div className="items-header">
                <span className="item-col">项目</span>
                <span className="qty-col">数量</span>
                <span className="price-col">单价</span>
                <span className="total-col">小计</span>
                <span className="action-col"></span>
              </div>
              
              {items.map((item, index) => (
                <div key={index} className="item-row">
                  <div className="item-col">
                    <select
                      value={item.projectId}
                      onChange={(e) => handleItemChange(index, 'projectId', e.target.value)}
                      required
                      disabled={isLoading || !formData.gameId}
                    >
                      <option value="">请选择项目</option>
                      {projects.map(project => (
                        <option key={project.id} value={project.id}>
                          {project.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="qty-col">
                    <input
                      type="number"
                      min="1"
                      value={item.quantity}
                      onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                      required
                      disabled={isLoading}
                    />
                  </div>
                  
                  <div className="price-col">
                    ¥{item.unitPrice.toFixed(2)}
                  </div>
                  
                  <div className="total-col">
                    ¥{(item.unitPrice * item.quantity).toFixed(2)}
                  </div>
                  
                  <div className="action-col">
                    <button
                      type="button"
                      onClick={() => handleRemoveItem(index)}
                      className="remove-item-btn"
                      disabled={isLoading || items.length <= 1}
                      title="删除"
                    >
                      ×
                    </button>
                  </div>
                </div>
              ))}
            </div>
            
            <button
              type="button"
              onClick={handleAddItem}
              className="add-item-btn"
              disabled={isLoading}
            >
              + 添加项目
            </button>
            
            <div className="order-total">
              <span>订单总额：</span>
              <span className="total-amount">¥{calculateTotal().toFixed(2)}</span>
            </div>
          </div>

          <div className="form-section">
            <h2>账号信息</h2>
            
            <div className="form-group">
              <label>游戏账号信息 *</label>
              <textarea
                value={formData.accountInfo}
                onChange={(e) => setFormData(prev => ({ ...prev, accountInfo: e.target.value }))}
                required
                disabled={isLoading}
                placeholder="请输入游戏账号、密码、服务器等信息..."
                rows="4"
              />
            </div>
          </div>

          <div className="form-section">
            <h2>其他要求</h2>
            
            <div className="form-group">
              <label>特殊要求</label>
              <textarea
                value={formData.requirements}
                onChange={(e) => setFormData(prev => ({ ...prev, requirements: e.target.value }))}
                disabled={isLoading}
                placeholder="例如：特定时间段、特定英雄等..."
                rows="3"
              />
            </div>
          </div>

          <div className="form-actions">
            <button
              type="button"
              onClick={handleBack}
              className="cancel-btn"
              disabled={isLoading}
            >
              取消
            </button>
            <button
              type="submit"
              className="submit-btn"
              disabled={isLoading}
            >
              {isLoading ? '发布中...' : '发布订单'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateOrder;
