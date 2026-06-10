import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
// 调用库函数：导入 QR 码生成组件（兜底备用）
// 传入：value（要编码的文本/URL），size（像素大小），level（纠错级别 L/M/Q/H）
// 作用：将传入的文本/URL 渲染为二维码 Canvas 图
// 传出：一个包含二维码的 Canvas DOM 元素
import { QRCodeCanvas } from 'qrcode.react';
import api from '../utils/api';
import './PaymentPage.css';

/**
 * 支付页面 - 使用 iaitouzi 聚合支付
 * 后端返回支付页面的真实二维码图片，前端直接展示
 */
const PaymentPage = () => {
  const { orderId } = useParams();
  const navigate = useNavigate();

  const [订单信息, set订单信息] = useState(null);
  const [联系方式, set联系方式] = useState('');
  const [支付方式, set支付方式] = useState('alipay');
  const [加载中, set加载中] = useState(true);
  const [支付中, set支付中] = useState(false);
  const [错误信息, set错误信息] = useState('');
  const [显示二维码弹窗, set显示二维码弹窗] = useState(false);
  const [支付链接, set支付链接] = useState('');
  const [二维码图片, set二维码图片] = useState('');  // 后端从支付页面提取的真实二维码图片（base64 data URL）
  const [轮询中, set轮询中] = useState(false);

  useEffect(() => {
    /** 加载订单详情 */
    const 加载订单信息 = async () => {
      set加载中(true);
      try {
        const 响应 = await api.get(`/orders/${orderId}`);
        const 数据 = 响应.data.data;
        set订单信息(数据);
        const 用户信息 = JSON.parse(localStorage.getItem('user') || '{}');
        if (用户信息.email) {
          set联系方式(用户信息.email);
        } else if (用户信息.phone) {
          set联系方式(用户信息.phone);
        } else if (数据.userName) {
          set联系方式(数据.userName);
        }
      } catch (错误) {
        console.error('加载订单失败:', 错误);
        set错误信息('加载订单信息失败');
      } finally {
        set加载中(false);
      }
    };
    加载订单信息();
  }, [orderId]);

  // 支付成功后轮询检测
  useEffect(() => {
    if (!轮询中 || !orderId) return;
    const 定时器 = setInterval(async () => {
      try {
        const 响应 = await api.get(`/payment/status/${orderId}`);
        const 记录列表 = 响应.data.data || [];
        if (记录列表.some(r => r.status === 'paid')) {
          clearInterval(定时器);
          set轮询中(false);
          set显示二维码弹窗(false);
          navigate(`/user/orders/${orderId}`);
        }
      } catch { /* 忽略轮询错误 */ }
    }, 3000);
    return () => clearInterval(定时器);
  }, [轮询中, orderId, navigate]);

  /** 发起支付 */
  const 发起支付 = async () => {
    if (!联系方式.trim()) {
      set错误信息('请输入联系方式');
      return;
    }
    if (联系方式.trim().length < 5) {
      set错误信息('联系方式长度至少 5 个字符');
      return;
    }

    set支付中(true);
    set错误信息('');

    const 是否有登录 = !!localStorage.getItem('token');
    const 支付接口路径 = 是否有登录 ? '/payment/create' : '/payment/anonymous/create';

    try {
      const 响应 = await api.post(支付接口路径, {
        订单ID: parseInt(orderId),
        支付方式: 支付方式,
        联系方式: 联系方式.trim(),
        重定向地址: `${window.location.origin}/user/orders/${orderId}`,
      });

      const { paymentUrl, qrCodeImage } = 响应.data.data;
      if (!paymentUrl) {
        throw new Error('未获取到支付链接');
      }

      set支付链接(paymentUrl);
      set二维码图片(qrCodeImage || '');  // 后端提取的真实二维码图片，无则置空
      set显示二维码弹窗(true);
      set轮询中(true);
    } catch (错误) {
      console.error('支付失败:', 错误);
      set错误信息(错误.response?.data?.message || '支付发起失败，请重试');
    } finally {
      set支付中(false);
    }
  };

  const 关闭二维码弹窗 = () => {
    set显示二维码弹窗(false);
    set轮询中(false);
    set支付链接('');
    set二维码图片('');
  };

  if (加载中) {
    return (
      <div className="payment-container">
        <div className="loading-state">加载中...</div>
      </div>
    );
  }

  if (!订单信息) {
    return (
      <div className="payment-container">
        <div className="error-state">
          <p>{错误信息 || '订单不存在'}</p>
          <button onClick={() => navigate(-1)} className="back-btn">返回</button>
        </div>
      </div>
    );
  }

  const 允许支付状态 = ['pending', 'pending_review'];

  return (
    <div className="payment-container">
      {/* 二维码支付弹窗 */}
      {显示二维码弹窗 && (
        <div className="qr-overlay" onClick={关闭二维码弹窗}>
          <div className="qr-modal" onClick={e => e.stopPropagation()}>
            <div className="qr-header">
              <h2>扫码支付</h2>
              <span className="qr-method-badge">
                {支付方式 === 'alipay' ? '支付宝' : '微信支付'}
              </span>
              <button className="qr-close-btn" onClick={关闭二维码弹窗}>✕</button>
            </div>
            <div className="qr-body">
              <p className="qr-amount">
                支付金额：<strong>¥{订单信息.totalAmount}</strong>
              </p>
              <p className="qr-tip">请使用{支付方式 === 'alipay' ? '支付宝' : '微信'}扫码支付</p>
              <div className="qr-code-container">
                {二维码图片 ? (
                  // 后端从支付页面提取的真实二维码图片，直接展示
                  // 传入：src=base64 data URL, alt=支付二维码
                  // 作用：展示支付页面的真实二维码图片，用户可直接扫码支付
                  // 传出：无返回值（直接渲染 img DOM 元素）
                  <img
                    src={二维码图片}
                    alt="支付二维码"
                    className="qr-code-image"
                    style={{ width: 240, height: 240, objectFit: 'contain' }}
                  />
                ) : (
                  // 兜底方案：后端未能提取二维码图片时，用支付链接生成二维码
                  // 传入：value=支付链接URL, size=240像素, level=M(中等纠错)
                  // 作用：将支付链接编码为二维码，用户扫码后跳转到支付页面
                  // 传出：包含二维码的 Canvas DOM 元素
                  <QRCodeCanvas value={支付链接} size={240} level="M" bgColor="#ffffff" fgColor="#000000" />
                )}
              </div>
              <p className="qr-hint">请截图或使用另一台设备扫码</p>
              <p className="qr-status-text">
                {轮询中 ? '等待扫码支付...' : '支付完成后请等待页面自动跳转'}
              </p>
            </div>
            <div className="qr-footer">
              <button className="qr-paid-btn" onClick={() => navigate(`/user/orders/${orderId}`)}>
                我已支付完成
              </button>
              <button className="qr-cancel-btn" onClick={关闭二维码弹窗}>
                取消支付
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="payment-card">
        <div className="payment-header">
          <button onClick={() => navigate(-1)} className="back-btn">← 返回</button>
          <h1>订单支付</h1>
        </div>

        {/* 订单摘要 */}
        <div className="order-summary">
          <div className="summary-row">
            <span className="summary-label">订单号</span>
            <span className="summary-value order-no">{订单信息.orderNo}</span>
          </div>
          <div className="summary-row">
            <span className="summary-label">游戏</span>
            <span className="summary-value">{订单信息.gameName || '-'}</span>
          </div>
          <div className="summary-row total-row">
            <span className="summary-label">支付金额</span>
            <span className="summary-value price">¥{订单信息.totalAmount}</span>
          </div>
        </div>

        {/* 支付方式选择 */}
        <div className="payment-methods">
          <h2 className="section-title">选择支付方式</h2>
          <div className="method-options">
            <label className={`method-option ${支付方式 === 'alipay' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="paymentMethod"
                value="alipay"
                checked={支付方式 === 'alipay'}
                onChange={() => set支付方式('alipay')}
              />
              <span className="method-icon alipay-icon">
                <svg viewBox="0 0 24 24" width="28" height="28" fill="none">
                  <rect width="24" height="24" rx="4" fill="#1677FF"/>
                  <text x="12" y="17" textAnchor="middle" fontSize="14" fontWeight="bold" fill="white">支</text>
                </svg>
              </span>
              <span className="method-name">支付宝</span>
            </label>
            <label className={`method-option ${支付方式 === 'wechat' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="paymentMethod"
                value="wechat"
                checked={支付方式 === 'wechat'}
                onChange={() => set支付方式('wechat')}
              />
              <span className="method-icon wechat-icon">
                <svg viewBox="0 0 24 24" width="28" height="28" fill="none">
                  <rect width="24" height="24" rx="4" fill="#07C160"/>
                  <text x="12" y="17" textAnchor="middle" fontSize="14" fontWeight="bold" fill="white">微</text>
                </svg>
              </span>
              <span className="method-name">微信支付</span>
            </label>
          </div>
        </div>

        {/* 联系方式 */}
        <div className="contact-section">
          <h2 className="section-title">联系方式</h2>
          <p className="section-desc">用于支付后找回订单</p>
          <input
            type="text"
            className="contact-input"
            placeholder="请输入邮箱或手机号"
            value={联系方式}
            onChange={(e) => set联系方式(e.target.value)}
          />
        </div>

        {/* 错误提示 */}
        {错误信息 && <div className="payment-error">{错误信息}</div>}

        {/* 操作按钮 */}
        <div className="payment-actions">
          {允许支付状态.includes(订单信息.status) ? (
            <button
              onClick={发起支付}
              disabled={支付中}
              className={`pay-btn ${支付中 ? 'loading' : ''}`}
            >
              {支付中 ? '正在获取支付二维码...' : `确认支付 ¥${订单信息.totalAmount}`}
            </button>
          ) : (
            <div className="cannot-pay-notice">
              当前订单状态 ({订单信息.status}) 不允许支付
            </div>
          )}
          <button onClick={() => navigate(`/user/orders/${orderId}`)} className="back-to-order-btn">
            返回订单详情
          </button>
        </div>

        {/* 支付提示 */}
        <div className="payment-tips">
          <h3>支付说明</h3>
          <ul>
            <li>选择支付方式后，点击"确认支付"即可看到支付二维码</li>
            <li>打开{支付方式 === 'alipay' ? '支付宝' : '微信'}扫码完成支付</li>
            <li>支付完成后页面自动跳转，无需手动操作</li>
            <li>如有任何问题，请联系客服</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default PaymentPage;
