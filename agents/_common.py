import uuid


def tokens(text: str) -> list[str]:
    words = text.split(" ")
    return [w if i == 0 else " " + w for i, w in enumerate(words)]


def call_id() -> str:
    return f"call_{uuid.uuid4().hex[:8]}"
