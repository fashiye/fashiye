import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Register.css';

const Register = () => {
  const [role, setRole] = useState('user');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [countdown, setCountdown] = useState(0);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSendingCode, setIsSendingCode] = useState(false);
  const navigate = useNavigate();

  const roles = [
    { value: 'user', label: '玩家' },
    { value: 'handler', label: '打手' }
  ];

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/auth/register`, {
        username,
        email,
        password,
        phone,
        role,
        verification_code: verificationCode
      });

      const token = response.data.access_token;
      localStorage.setItem('token', token);
      localStorage.setItem('role', role);
      localStorage.setItem('user', JSON.stringify(response.data.user));

      window.dispatchEvent(new Event('auth-change'));

      switch (role) {
        case 'user':
          navigate('/user');
          break;
        case 'handler':
          navigate('/handler');
          break;
        default:
          navigate('/user');
      }
    } catch (err) {
      setError('注册失败，请检查输入信息');
      console.error('Register error:', err);
      if (err.response) {
        console.error('Response data:', err.response.data);
        console.error('Response status:', err.response.status);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToLogin = () => {
    navigate('/');
  };

  const handleSendCode = async () => {
    if (!email) {
      setError('请输入邮箱');
      return;
    }

    setIsSendingCode(true);
    try {
      await axios.post(`${import.meta.env.VITE_API_BASE_URL}/auth/send-code`, {
        email
      });
      setError('');
      // 开始倒计时
      setCountdown(60);
      const timer = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } catch (err) {
      console.error('发送验证码失败:', err);
      setError(err.response?.data?.detail || '发送验证码失败');
    } finally {
      setIsSendingCode(false);
    }
  };

  return (
    <div className="register-container">
      <div className="register-card">
        <h2>游戏代练交易平台</h2>
        <p className="subtitle">请选择角色并注册</p>

        <div className="role-selector">
          {roles.map((roleOption) => (
            <button
              key={roleOption.value}
              className={`role-btn ${role === roleOption.value ? 'active' : ''}`}
              onClick={() => setRole(roleOption.value)}
            >
              {roleOption.label}
            </button>
          ))}
        </div>

        <form onSubmit={handleRegister} className="register-form">
          {error && <div className="error-message">{error}</div>}

          <div className="input-group">
            <label>用户名</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <div className="input-group">
            <label>邮箱</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <div className="input-group">
            <label>验证码</label>
            <div style={{ display: 'flex', gap: '10px' }}>
              <input
                type="text"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value)}
                placeholder="请输入验证码"
                required
                disabled={isLoading}
                style={{ flex: 1 }}
              />
              <button
                type="button"
                onClick={handleSendCode}
                disabled={countdown > 0 || isSendingCode || isLoading || !email}
                style={{
                  padding: '0 16px',
                  background: countdown > 0 ? '#e5e7eb' : '#6366f1',
                  color: countdown > 0 ? '#6b7280' : 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: countdown > 0 ? 'not-allowed' : 'pointer',
                  fontSize: '13px',
                  fontWeight: '500'
                }}
              >
                {isSendingCode ? '发送中...' : countdown > 0 ? `${countdown}s后重发` : '发送验证码'}
              </button>
            </div>
          </div>

          <div className="input-group">
            <label>手机号</label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              disabled={isLoading}
            />
          </div>

          <div className="input-group">
            <label>密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <button 
            type="submit" 
            className="register-btn"
            disabled={isLoading}
          >
            {isLoading ? '注册中...' : '注册'}
          </button>
        </form>

        <div className="login-link">
          已有账号？ <button onClick={handleBackToLogin} className="link-btn">立即登录</button>
        </div>
      </div>
    </div>
  );
};

export default Register;
