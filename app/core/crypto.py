import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from app.core.config import settings


class AccountCrypto:
    def __init__(self):
        self.key = base64.b64decode(settings.AES_SECRET_KEY)
        iv_bytes = base64.b64decode(settings.AES_IV)
        self.iv = iv_bytes[:16].ljust(16, b'\x00')[:16]

    def encrypt(self, plain_text: str) -> str:
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        padded_data = pad(plain_text.encode('utf-8'), AES.block_size)
        encrypted_bytes = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted_bytes).decode('utf-8')

    def decrypt(self, encrypted_text: str) -> str:
        encrypted_bytes = base64.b64decode(encrypted_text)
        cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        decrypted_padded = cipher.decrypt(encrypted_bytes)
        return unpad(decrypted_padded, AES.block_size).decode('utf-8')


crypto = AccountCrypto()
