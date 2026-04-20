import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Login.css';

const AUTH_CHANGE_EVENT = 'auth:changed';

const Login = () => {
  const [role, setRole] = useState('user');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError('');
      }, 30000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  const roles = [
    { value: 'user', label: '玩家' },
    { value: 'handler', label: '打手' },
    { value: 'admin', label: '管理员' }
  ];

  const clearForm = () => {
    setUsername('');
    setPassword('');
    setError('');
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    if (!username.trim()) {
      setError('请输入用户名');
      return;
    }

    if (!password) {
      setError('请输入密码');
      return;
    }

    setIsLoading(true);

    try {
      const response = await axios.post(`${import.meta.env.VITE_API_BASE_URL}/auth/login`, {
        username,
        password,
        role
      });

      const token = response.data.access_token;
      const actualRole = response.data.user.role;
      localStorage.setItem('token', token);
      localStorage.setItem('role', actualRole);
      localStorage.setItem('user', JSON.stringify(response.data.user));

      window.dispatchEvent(new Event(AUTH_CHANGE_EVENT));

      clearForm();

      switch (actualRole) {
        case 'user':
          navigate('/user');
          break;
        case 'handler':
          navigate('/handler');
          break;
        case 'admin':
          navigate('/admin');
          break;
        default:
          navigate('/user');
      }
    } catch (err) {
      let errorMsg = '登录失败，请检查用户名和密码';
      
      if (!err.response) {
        errorMsg = '网络连接失败，请检查网络设置';
      } else if (err.response.status === 401) {
        errorMsg = '用户名或密码错误';
      } else if (err.response.status === 403) {
        errorMsg = '账号已被禁用，请联系管理员';
      } else if (err.response.status === 429) {
        errorMsg = '登录尝试过于频繁，请稍后再试';
      } else if (err.response.status === 500) {
        errorMsg = '服务器错误，请稍后再试';
      } else if (err.response.data?.message) {
        errorMsg = err.response.data.message;
      } else if (err.response.data?.detail) {
        errorMsg = err.response.data.detail;
      }
      
      setError(errorMsg);
      console.error('Login error:', err);
      if (err.response) {
        console.error('Response data:', err.response.data);
        console.error('Response status:', err.response.status);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>游戏代练交易平台</h2>
        <p className="subtitle">请选择角色并登录</p>

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

        <form onSubmit={handleLogin} className="login-form">
          {error && <div className="error-message">{error}</div>}

          <div className="input-group">
            <label>用户名</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              disabled={isLoading}
              minLength={3}
              maxLength={50}
              placeholder="请输入用户名"
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
              minLength={6}
              placeholder="请输入密码"
            />
          </div>

          <button 
            type="submit" 
            className="login-btn"
            disabled={isLoading}
          >
            {isLoading ? '登录中...' : '登录'}
          </button>
        </form>

        <div className="register-link">
          还没有账号？ <a href="/register">立即注册</a>
        </div>

        <div className="forgot-password-link">
          <a href="/forgot-password">忘记密码？</a>
        </div>
      </div>
    </div>
  );
};

export default Login;
