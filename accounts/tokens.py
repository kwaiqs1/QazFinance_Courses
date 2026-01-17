from django.core.signing import TimestampSigner, BadSignature, SignatureExpired

signer = TimestampSigner(salt="qazfinance.email.verify")

def make_token(user_id: int) -> str:
    return signer.sign(str(user_id))

def verify_token(token: str, max_age_seconds: int = 60 * 60 * 48) -> int | None:
    try:
        raw = signer.unsign(token, max_age=max_age_seconds)
        return int(raw)
    except (BadSignature, SignatureExpired):
        return None
