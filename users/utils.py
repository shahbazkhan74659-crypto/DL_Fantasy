import hashlib

GRAVATAR_URL = 'https://www.gravatar.com/avatar/{digest}?s={size}&d={default}'


def gravatar_hash(email: str) -> str:
    return hashlib.md5(email.strip().lower().encode('utf-8')).hexdigest()


def gravatar_url(email: str, size: int = 160, default: str = 'mp') -> str:
    return GRAVATAR_URL.format(digest=gravatar_hash(email), size=size, default=default)
