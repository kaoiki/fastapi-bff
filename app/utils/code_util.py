import random
from app.core.config import settings


def generate_code() -> str:
    length = settings.verification_code_length
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])