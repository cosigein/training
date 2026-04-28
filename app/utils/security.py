import secrets
import hashlib

def generate_api_key():
    """Genera una API key segura y su hash."""
    prefix = secrets.token_hex(4)
    raw_key = f"db_{prefix}_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    return {
        "raw": raw_key,
        "hash": key_hash,
        "prefix": prefix
    }
