#!/usr/bin/env python3
"""Create demo student and admin users in Supabase."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

SUPABASE_URL = os.environ.get("SUPABASE_URL", "http://127.0.0.1:54321").rstrip("/")
SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
STORAGE_BUCKET = os.environ.get("STORAGE_BUCKET", "question-images")

DEMO_USERS = [
    {
        "email": "demo@aditi.dev",
        "password": "Demo123456!",
        "role": "student",
    },
    {
        "email": "admin@aditi.dev",
        "password": "Admin123456!",
        "role": "admin",
    },
]


def request(method: str, path: str, payload: dict | None = None) -> dict:
    body = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{SUPABASE_URL}{path}",
        data=body,
        method=method,
        headers={
            "apikey": SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as response:
            raw = response.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()
        raise RuntimeError(f"{method} {path} failed ({exc.code}): {detail}") from exc


def ensure_bucket() -> None:
    try:
        request(
            "POST",
            "/storage/v1/bucket",
            {"name": STORAGE_BUCKET, "public": False},
        )
        print(f"Created storage bucket: {STORAGE_BUCKET}")
    except RuntimeError as exc:
        if "already exists" in str(exc).lower() or "duplicate" in str(exc).lower():
            print(f"Storage bucket already exists: {STORAGE_BUCKET}")
            return
        raise


def ensure_user(email: str, password: str) -> None:
    try:
        request(
            "POST",
            "/auth/v1/admin/users",
            {
                "email": email,
                "password": password,
                "email_confirm": True,
            },
        )
        print(f"Created user: {email}")
    except RuntimeError as exc:
        if "already been registered" in str(exc).lower() or "already exists" in str(exc).lower():
            print(f"User already exists: {email}")
            return
        raise


def main() -> int:
    if not SERVICE_ROLE_KEY:
        print("SUPABASE_SERVICE_ROLE_KEY is required", file=sys.stderr)
        return 1

    ensure_bucket()
    for user in DEMO_USERS:
        ensure_user(user["email"], user["password"])

    print("\nDemo credentials:")
    for user in DEMO_USERS:
        print(f"  {user['role'].title():8}  {user['email']}  /  {user['password']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
