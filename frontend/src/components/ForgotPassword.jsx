import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './ForgotPassword.css';

const EMAIL_REGEX = /^\S+@\S+\.\S+$/;

const ForgotPassword = () => {
  const [role, setRole] = useState('user');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(''), 30000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(''), 30000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  const roles = [
    { value: 'user', label: '玩家' },
    { value: 'handler', label: '打手' },
    { value: 'admin', label: '管理员' }
  ];

  const validateEmail = (email) => {
    return EMAIL_REGEX.test(email);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!email) {
      setError('请输入邮箱');
      return;
    }

    if (!validateEmail(email)) {
      setError('请输入有效的邮箱地址');
      return;
    }

    setIsLoading(true);

    try {
      await axios.post(`${import.meta.env.VITE_API_BASE_URL}/auth/forgot-password`, {
        email,
        role
      });

      setSuccess('密码重置验证码已发送到您的邮箱，请查收');
      setTimeout(() => {
        navigate(`/reset-password?email=${encodeURIComponent(email)}&role=${role}`);
      }, 2000);
    } catch (err) {
      let errorMsg = '发送验证码失败';
      
      if (!err.response) {
        errorMsg = '网络连接失败，请检查网络设置';
      } else if (err.response.status === 429) {
        errorMsg = '请求过于频繁，请稍后再试';
      } else if (err.response.data?.message) {
        errorMsg = err.response.data.message;
      } else if (err.response.data?.detail) {
        errorMsg = err.response.data.detail;
      }
      
      setError(errorMsg);
      console.error('Forgot password error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToLogin = () => {
    navigate('/');
  };

  return (
    <div className="forgot-password-container">
      <div className="forgot-password-card">
        <h2>找回密码</h2>
        <p className="subtitle">请输入您的注册邮箱</p>

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

        <form onSubmit={handleSubmit} className="forgot-password-form">
          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}

          <div className="input-group">
            <label>邮箱</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isLoading}
              placeholder="请输入注册邮箱"
            />
          </div>

          <button 
            type="submit" 
            className="submit-btn"
            disabled={isLoading}
          >
            {isLoading ? '发送中...' : '发送验证码'}
          </button>
        </form>

        <div className="back-link">
          <button onClick={handleBackToLogin} className="link-btn">返回登录</button>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
