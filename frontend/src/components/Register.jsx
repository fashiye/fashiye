import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Register.css';

const AUTH_CHANGE_EVENT = 'auth:changed';

const EMAIL_REGEX = /^\S+@\S+\.\S+$/;
const PHONE_REGEX = /^1[3-9]\d{9}$/;
const PASSWORD_MIN_LENGTH = 6;

const Register = () => {
  const [role, setRole] = useState('user');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [countdown, setCountdown] = useState(0);
  const [sentEmail, setSentEmail] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSendingCode, setIsSendingCode] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => {
        setError('');
      }, 30000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  useEffect(() => {
    let timer;
    if (countdown > 0) {
      timer = setInterval(() => {
        setCountdown(prev => prev - 1);
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [countdown]);

  useEffect(() => {
    if (sentEmail && email !== sentEmail) {
      setCountdown(0);
      setSentEmail('');
    }
  }, [email, sentEmail]);

  const roles = [
    { value: 'user', label: '玩家' },
    { value: 'handler', label: '打手' }
  ];

  const validateEmail = (email) => {
    return EMAIL_REGEX.test(email);
  };

  const validatePhone = (phone) => {
    return !phone || PHONE_REGEX.test(phone);
  };

  const validatePassword = (password) => {
    if (password.length < PASSWORD_MIN_LENGTH) {
      return { valid: false, message: `密码长度至少${PASSWORD_MIN_LENGTH}位` };
    }
    if (!/[a-zA-Z]/.test(password)) {
      return { valid: false, message: '密码必须包含字母' };
    }
    if (!/\d/.test(password)) {
      return { valid: false, message: '密码必须包含数字' };
    }
    return { valid: true, message: '' };
  };

  const getPasswordStrength = (password) => {
    if (!password) return { level: 0, text: '', color: '' };
    
    let strength = 0;
    
    if (password.length >= PASSWORD_MIN_LENGTH) strength++;
    if (password.length >= 8) strength++;
    if (password.length >= 12) strength++;
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/\d/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;

    if (strength <= 3) return { level: 1, text: '弱', color: '#ef4444' };
    if (strength <= 5) return { level: 2, text: '中', color: '#f59e0b' };
    return { level: 3, text: '强', color: '#10b981' };
  };

  const clearForm = () => {
    setUsername('');
    setEmail('');
    setPassword('');
    setPhone('');
    setVerificationCode('');
    setCountdown(0);
    setSentEmail('');
    setError('');
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');

    if (!validateEmail(email)) {
      setError('请输入有效的邮箱地址');
      return;
    }

    if (!validatePhone(phone)) {
      setError('请输入有效的手机号码');
      return;
    }

    const passwordValidation = validatePassword(password);
    if (!passwordValidation.valid) {
      setError(passwordValidation.message);
      return;
    }

    if (!sentEmail || email !== sentEmail) {
      setError('请先发送验证码到当前邮箱');
      return;
    }

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

      window.dispatchEvent(new Event(AUTH_CHANGE_EVENT));

      clearForm();

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
      let errorMsg = '注册失败，请检查输入信息';
      
      if (!err.response) {
        errorMsg = '网络连接失败，请检查网络设置';
      } else if (err.response.status === 429) {
        errorMsg = '请求过于频繁，请稍后再试';
      } else if (err.response.status === 500) {
        errorMsg = '服务器错误，请稍后再试';
      } else if (err.response.data?.message) {
        errorMsg = err.response.data.message;
      } else if (err.response.data?.detail) {
        errorMsg = err.response.data.detail;
      }
      
      setError(errorMsg);
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

    if (!validateEmail(email)) {
      setError('请输入有效的邮箱地址');
      return;
    }

    setIsSendingCode(true);
    try {
      await axios.post(`${import.meta.env.VITE_API_BASE_URL}/auth/send-code`, {
        email
      });
      setError('');
      setSentEmail(email);
      setCountdown(60);
    } catch (err) {
      let errorMsg = '发送验证码失败';
      
      if (!err.response) {
        errorMsg = '网络连接失败，请检查网络设置';
      } else if (err.response.status === 429) {
        errorMsg = '请求过于频繁，请60秒后再试';
      } else if (err.response.status === 400) {
        errorMsg = '邮箱地址无效';
      } else if (err.response.data?.message) {
        errorMsg = err.response.data.message;
      } else if (err.response.data?.detail) {
        errorMsg = err.response.data.detail;
      }
      
      setError(errorMsg);
      console.error('发送验证码失败:', err);
    } finally {
      setIsSendingCode(false);
    }
  };

  const passwordStrength = getPasswordStrength(password);

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
              minLength={3}
              maxLength={50}
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
              placeholder="example@email.com"
            />
          </div>

          <div className="input-group">
            <label>验证码</label>
            <div className="verification-code-group">
              <input
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
                placeholder="请输入验证码"
                required
                disabled={isLoading}
                className="verification-input"
              />
              <button
                type="button"
                onClick={handleSendCode}
                disabled={countdown > 0 || isSendingCode || isLoading || !email}
                className={`send-code-btn ${countdown > 0 ? 'countdown' : ''}`}
              >
                {isSendingCode ? '发送中...' : countdown > 0 ? `${countdown}s后重发` : '发送验证码'}
              </button>
            </div>
            {sentEmail && email === sentEmail && (
              <div className="hint-message">验证码已发送至 {sentEmail}</div>
            )}
          </div>

          <div className="input-group">
            <label>手机号（选填）</label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              disabled={isLoading}
              placeholder="请输入11位手机号"
              maxLength={11}
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
              minLength={PASSWORD_MIN_LENGTH}
              placeholder={`至少${PASSWORD_MIN_LENGTH}位，包含字母和数字`}
            />
            {password && (
              <div className="password-strength">
                <div className="strength-bar">
                  <div 
                    className="strength-fill"
                    style={{ 
                      width: `${(passwordStrength.level / 3) * 100}%`,
                      backgroundColor: passwordStrength.color 
                    }}
                  />
                </div>
                <span style={{ color: passwordStrength.color }}>
                  {passwordStrength.text}
                </span>
              </div>
            )}
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
