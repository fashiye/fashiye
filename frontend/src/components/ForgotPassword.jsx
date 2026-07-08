import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/api';
import 样式 from './ForgotPassword.module.css';

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
      await api.post('/auth/forgot-password', {
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
    <div className={样式.forgotPasswordContainer}>
      <div className={样式.forgotPasswordCard}>
        <h2>忘记密码</h2>
        <p className={样式.subtitle}>请输入您的注册邮箱</p>
        <div className={样式.roleSelector}>
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

        <form onSubmit={handleSubmit} className={样式.forgotPasswordForm}>
          {error && <div className={样式.errorMessage}>{error}</div>}
          {success && <div className={样式.successMessage}>{success}</div>}

          <div className={样式.inputGroup}>
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
            className={样式.submitBtn}
            disabled={isLoading}
          >
            {isLoading ? '发送中...' : '发送验证码'}
          </button>
        </form>

        <div className={样式.backLink}>
          <button onClick={handleBackToLogin} className={样式.linkBtn}>返回登录</button>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
