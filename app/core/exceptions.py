from fastapi import HTTPException, status


class BusinessError(Exception):
    def __init__(self, message: str, code: int = 400):
        self.message = message
        self.code = code


class AuthError(Exception):
    def __init__(self, message: str, code: int = 401):
        self.message = message
        self.code = code
