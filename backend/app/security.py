from __future__ import annotations


def build_security_headers(*, app_env: str) -> dict[str, str]:
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
    }
    if app_env.lower() == "production":
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return headers
