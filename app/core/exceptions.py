class AppException(Exception):
    def __init__(self, message: str = "error", code: int = 400, data=None):
        self.code = code
        self.message = message
        self.data = data