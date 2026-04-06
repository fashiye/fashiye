import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Login.css';

const Login = () => {
  const [role, setRole] = useState('user'); // user, handler, admin
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const roles = [
    { value: 'user', label: '玩家' },
    { value: 'handler', label: '打手' },
    { value: 'admin', label: '管理员' }
  ];

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
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

      window.dispatchEvent(new Event('auth-change'));

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
      setError('登录失败，请检查用户名和密码');
      console.error('Login error:', err);
      // 打印详细错误信息
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

        {/* 角色选择滚轮 */}
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

        {/* 登录表单 */}
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
            className="login-btn"
            disabled={isLoading}
          >
            {isLoading ? '登录中...' : '登录'}
          </button>
        </form>

        <div className="register-link">
          还没有账号？ <a href="/register">立即注册</a>
        </div>
      </div>
    </div>
  );
};

export default Login;