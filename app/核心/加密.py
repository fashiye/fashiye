import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from app.核心.配置 import 配置对象


class 账号信息加解密类:
    """
    使用 AES-CBC 模式对账号敏感信息进行加解密
    """

    def __init__(self):
        """初始化加解密器，从配置加载密钥和向量"""
        self.密钥 = base64.b64decode(配置对象.AES密钥)
        向量字节 = base64.b64decode(配置对象.AES向量)
        self.向量 = 向量字节[:16].ljust(16, b'\x00')[:16]

    def 加密(self, 明文: str) -> str:
        """
        使用 AES-CBC 加密明文

        Args:
            明文: 待加密的字符串

        Returns:
            Base64 编码的加密字符串
        """
        加密器 = AES.new(self.密钥, AES.MODE_CBC, self.向量)
        填充后数据 = pad(明文.encode('utf-8'), AES.block_size)
        加密后字节 = 加密器.encrypt(填充后数据)
        return base64.b64encode(加密后字节).decode('utf-8')

    def 解密(self, 密文: str) -> str:
        """
        解密 AES-CBC 加密的密文

        Args:
            密文: Base64 编码的加密字符串

        Returns:
            解密后的明文字符串
        """
        加密后字节 = base64.b64decode(密文)
        解密器 = AES.new(self.密钥, AES.MODE_CBC, self.向量)
        解密后填充数据 = 解密器.decrypt(加密后字节)
        return unpad(解密后填充数据, AES.block_size).decode('utf-8')


加解密工具 = 账号信息加解密类()
