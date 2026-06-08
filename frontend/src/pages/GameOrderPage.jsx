import React, { useState, useEffect, useCallback } from 'react';
import api from '../utils/api';
import './GameOrderPage.css';

const GameOrderPage = () => {
  const [step, setStep] = useState(1);
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
  const [successData, setSuccessData] = useState(null);
  const [copied, setCopied] = useState(false);

  const fetchGames = useCallback(async () => {
    try {
      const response = await api.get('/games');
      setGames(response.data);
      if (response.data.length > 0) {
        setFormData(prev => ({ ...prev, gameId: response.data[0].id }));
        fetchProjects(response.data[0].id);
      }
    } catch (err) {
      console.error('获取游戏列表失败:', err);
      setError('获取游戏列表失败，请刷新重试');
    }
  }, []);

  const fetchProjects = async (gameId) => {
    try {
      const response = await api.get(`/games/${gameId}/projects`);
      setProjects(response.data);
    } catch (err) {
      console.error('获取项目列表失败:', err);
      setError('获取项目列表失败');
    }
  };

  useEffect(() => {
    fetchGames();
  }, [fetchGames]);

  const handleGameChange = (e) => {
    const gameId = e.target.value;
    setFormData(prev => ({ ...prev, gameId }));
    fetchProjects(gameId);
    setItems([{ projectId: '', quantity: 1, unitPrice: 0 }]);
    setError('');
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
      
      if (field === 'projectId') {
        const project = projects.find(p => p.id === parseInt(value));
        newItems[index].unitPrice = project ? project.price : 0;
      }
      
      return newItems;
    });
    setError('');
  };

  const calculateTotal = () => {
    return items.reduce((total, item) => {
      return total + (item.unitPrice * item.quantity);
    }, 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    const validItems = items.filter(item => item.projectId && item.quantity >= 1);
    if (validItems.length === 0) {
      setError('请至少选择一个项目');
      return;
    }

    if (!formData.accountInfo.trim()) {
      setError('请填写账号信息');
      return;
    }

    setIsLoading(true);
    
    try {
      const response = await api.post('/orders/anonymous', {
        gameId: parseInt(formData.gameId),
        accountInfo: formData.accountInfo,
        requirements: formData.requirements || '',
        items: validItems.map(item => ({
          projectId: parseInt(item.projectId),
          quantity: item.quantity
        }))
      });
      
      setSuccessData({
        orderNo: response.data.data.orderNo,
        orderId: response.data.data.orderId,
        totalAmount: calculateTotal()
      });
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.detail || '下单失败，请重试');
    } finally {
      setIsLoading(false);
    }
  };

  const copyOrderNo = () => {
    if (successData?.orderNo) {
      try {
        // 传入：successData.orderNo（要复制的凭据号字符串）
        // 作用：创建临时 input 元素，用传统 execCommand 方式复制到剪贴板（兼容非 HTTPS 环境）
        // 传出：如果 navigator.clipboard 可用则优先使用，否则降级到 document.execCommand
        const 临时输入框 = document.createElement('textarea');
        临时输入框.value = successData.orderNo;
        临时输入框.style.position = 'fixed';
        临时输入框.style.opacity = '0';
        document.body.appendChild(临时输入框);
        临时输入框.select();
        document.execCommand('copy');
        document.body.removeChild(临时输入框);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        console.error('复制失败:', err);
        alert('复制失败，请手动复制凭据号');
      }
    }
  };

  const goBack = () => {
    setStep(1);
    setSuccessData(null);
  };

  return (
    <div className="game-order-container">
      {step === 1 && (
        <div className="order-form">
          <h1 className="title">游戏代练下单</h1>
          
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>选择游戏</label>
              <select
                value={formData.gameId}
                onChange={handleGameChange}
                className="form-control"
              >
                <option value="">请选择游戏</option>
                {games.map(game => (
                  <option key={game.id} value={game.id}>
                    {game.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>选择项目</label>
              <div className="items-container">
                {items.map((item, index) => (
                  <div key={index} className="item-row">
                    <select
                      value={item.projectId}
                      onChange={(e) => handleItemChange(index, 'projectId', e.target.value)}
                      className="form-control item-select"
                    >
                      <option value="">请选择项目</option>
                      {projects.map(project => (
                        <option key={project.id} value={project.id}>
                          {project.name} - {project.price}元
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      min="1"
                      value={item.quantity}
                      onChange={(e) => handleItemChange(index, 'quantity', parseInt(e.target.value) || 1)}
                      className="form-control quantity-input"
                      placeholder="数量"
                    />
                    <span className="price-display">
                      {(item.unitPrice * item.quantity).toFixed(2)}元
                    </span>
                    {items.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveItem(index)}
                        className="remove-btn"
                      >
                        ×
                      </button>
                    )}
                  </div>
                ))}
              </div>
              <button
                type="button"
                onClick={handleAddItem}
                className="add-item-btn"
              >
                + 添加项目
              </button>
            </div>

            <div className="form-group">
              <label>账号信息</label>
              <textarea
                value={formData.accountInfo}
                onChange={(e) => setFormData(prev => ({ ...prev, accountInfo: e.target.value }))}
                className="form-control textarea"
                placeholder="请输入游戏账号和密码（我们会加密存储）"
              />
            </div>

            <div className="form-group">
              <label>需求描述（选填）</label>
              <textarea
                value={formData.requirements}
                onChange={(e) => setFormData(prev => ({ ...prev, requirements: e.target.value }))}
                className="form-control textarea"
                placeholder="请描述你的具体需求..."
              />
            </div>

            <div className="total-section">
              <span className="total-label">订单总额：</span>
              <span className="total-amount">¥{calculateTotal().toFixed(2)}</span>
            </div>

            {error && <div className="error-message">{error}</div>}
            
            <button
              type="submit"
              disabled={isLoading}
              className="submit-btn"
            >
              {isLoading ? '提交中...' : '立即下单'}
            </button>
          </form>
        </div>
      )}

      {step === 2 && successData && (
        <div className="success-container">
          <div className="success-icon">✓</div>
          <h2 className="success-title">下单成功！</h2>
          <p className="success-desc">您的订单已提交，请妥善保管您的凭据号</p>
          
          <div className="order-info">
            <div className="order-no-section">
              <span className="order-label">凭据号：</span>
              <span className="order-no">{successData.orderNo}</span>
            </div>
            
            <div className="total-info">
              订单金额：¥{successData.totalAmount.toFixed(2)}
            </div>

            <button
              onClick={copyOrderNo}
              className="copy-btn"
            >
              {copied ? '✓ 已复制' : '一键复制'}
            </button>
          </div>

          <div className="tips">
            <div className="tip-item">
              <span className="tip-icon">📷</span>
              <span>请截图保存此凭据号</span>
            </div>
            <div className="tip-item">
              <span className="tip-icon">🔗</span>
              <span>访问 docs.fashiye.com 查询订单状态</span>
            </div>
          </div>

          <button onClick={goBack} className="back-btn">
            返回继续下单
          </button>
        </div>
      )}
    </div>
  );
};

export default GameOrderPage;
