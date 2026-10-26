#!/usr/bin/env python3
"""
Staging Smoke Test Runner for AI Accountability Pipeline.

Runs as a CI verification job following staging deployment.
Executes in-process smoke tests against the Flask inventory microservice
(or targets an external HTTP URL if specified).
Includes a --fail-on-purpose flag to simulate post-deployment incident triage
(Demo Scenario C) without needing live external infrastructure.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Ensure repository root is on sys.path for in-process app imports
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def run_in_process_smoke_test(fail_on_purpose: bool = False) -> Tuple[bool, str]:
    """Runs smoke tests against the application in-process using Flask test client."""
    try:
        from src.app import create_app
    except ImportError as e:
        return False, f"Failed to import application package: {e}"

    if fail_on_purpose:
        return (
            False,
            "CRITICAL: Healthcheck failed! Simulated staging incident (--fail-on-purpose flag active). "
            "Inventory service /health returned 500 Internal Server Error (unhandled database connection pool exhaustion).",
        )

    app = create_app({"TESTING": True})
    client = app.test_client()

    # 1. Healthcheck probe
    res = client.get("/health")
    if res.status_code != 200:
        return False, f"Healthcheck failed: GET /health returned HTTP {res.status_code}"
    data = res.get_json() or {}
    if data.get("status") != "healthy":
        return False, f"Healthcheck payload invalid: expected 'healthy', got '{data.get('status')}'"

    # 2. Root metadata probe
    res_root = client.get("/")
    if res_root.status_code != 200:
        return False, f"Root probe failed: GET / returned HTTP {res_root.status_code}"

    # 3. Inventory items probe
    res_items = client.get("/items")
    if res_items.status_code != 200:
        return False, f"Inventory probe failed: GET /items returned HTTP {res_items.status_code}"
    items_data = res_items.get_json() or {}
    if "items" not in items_data:
        return False, "Inventory payload invalid: 'items' array missing"

    return True, f"All smoke tests passed (in-process). Probed: /health, /, /items. Found {items_data.get('count', 0)} items."


def run_http_smoke_test(base_url: str, fail_on_purpose: bool = False) -> Tuple[bool, str]:
    """Runs smoke tests against an active HTTP URL."""
    import urllib.request
    import urllib.error

    if fail_on_purpose:
        return (
            False,
            "CRITICAL: Healthcheck failed! Simulated staging incident (--fail-on-purpose flag active). "
            "Endpoint returned HTTP 500 Internal Server Error.",
        )

    health_url = base_url.rstrip("/") + "/health"
    try:
        req = urllib.request.Request(health_url, headers={"User-Agent": "GitLab-SmokeTest/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                return False, f"GET {health_url} returned HTTP {resp.status}"
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            if data.get("status") != "healthy":
                return False, f"Healthcheck payload invalid: {data}"
    except Exception as e:
        return False, f"HTTP smoke test failed connecting to {health_url}: {e}"

    return True, f"HTTP healthcheck passed: {health_url} returned 200 OK"


def main() -> None:
    parser = argparse.ArgumentParser(description="Staging Smoke Test Runner for DevSecOps Pipeline")
    parser.add_argument(
        "--url",
        default=None,
        help="Optional external HTTP URL to test (defaults to in-process Flask test client)",
    )
    parser.add_argument(
        "--fail-on-purpose",
        action="store_true",
        help="Deliberately simulate an unhealthy staging release for incident triage demonstration",
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("           STAGING SMOKE TEST & HEALTHCHECK")
    print("=" * 60)
    print(f"Target: {'HTTP ' + args.url if args.url else 'In-process Flask application package'}")
    print(f"Mode:   {'SIMULATE FAILURE (--fail-on-purpose)' if args.fail_on_purpose else 'Normal healthcheck verification'}")
    print("-" * 60)

    if args.url:
        success, message = run_http_smoke_test(args.url, fail_on_purpose=args.fail_on_purpose)
    else:
        success, message = run_in_process_smoke_test(fail_on_purpose=args.fail_on_purpose)

    if success:
        print(f"RESULT: PASSED\nDetails: {message}")
        print("=" * 60 + "\n")
        sys.exit(0)
    else:
        print(f"RESULT: FAILED\nDetails: {message}", file=sys.stderr)
        print("=" * 60 + "\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
