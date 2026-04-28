import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../utils/api';
import './ResetPassword.css';

const PASSWORD_MIN_LENGTH = 6;

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const email = searchParams.get('email') || '';
  const role = searchParams.get('role') || 'user';
  
  const [verificationCode, setVerificationCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!verificationCode) {
      setError('请输入验证码');
      return;
    }

    if (!newPassword) {
      setError('请输入新密码');
      return;
    }

    const passwordValidation = validatePassword(newPassword);
    if (!passwordValidation.valid) {
      setError(passwordValidation.message);
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('两次输入的密码不一致');
      return;
    }

    setIsLoading(true);

    try {
      await api.post('/auth/reset-password', {
        email,
        role,
        verification_code: verificationCode,
        new_password: newPassword
      });

      setSuccess('密码重置成功！即将跳转到登录页面...');
      setTimeout(() => {
        navigate('/');
      }, 2000);
    } catch (err) {
      let errorMsg = '密码重置失败';
      
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
      console.error('Reset password error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToLogin = () => {
    navigate('/');
  };

  const passwordStrength = getPasswordStrength(newPassword);

  return (
    <div className="reset-password-container">
      <div className="reset-password-card">
        <h2>重置密码</h2>
        <p className="subtitle">为账号 {email} 设置新密码</p>

        <form onSubmit={handleSubmit} className="reset-password-form">
          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">{success}</div>}

          <div className="input-group">
            <label>验证码</label>
            <input
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              value={verificationCode}
              onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, ''))}
              placeholder="请输入验证码"
              required
              disabled={isLoading}
              maxLength={6}
            />
          </div>

          <div className="input-group">
            <label>新密码</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              disabled={isLoading}
              minLength={PASSWORD_MIN_LENGTH}
              placeholder={`至少${PASSWORD_MIN_LENGTH}位，包含字母和数字`}
            />
            {newPassword && (
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

          <div className="input-group">
            <label>确认密码</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              disabled={isLoading}
              minLength={PASSWORD_MIN_LENGTH}
              placeholder="请再次输入新密码"
            />
          </div>

          <button 
            type="submit" 
            className="submit-btn"
            disabled={isLoading}
          >
            {isLoading ? '重置中...' : '重置密码'}
          </button>
        </form>

        <div className="back-link">
          <button onClick={handleBackToLogin} className="link-btn">返回登录</button>
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;
