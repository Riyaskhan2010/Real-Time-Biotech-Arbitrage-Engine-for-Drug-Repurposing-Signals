# -*- coding: utf-8 -*-
"""
Deep env-loading diagnostic.
NEVER prints the key value. Reports only: present/absent, length, loaded state.
"""
import sys, os, re

sys.path.insert(0, os.path.dirname(__file__))
backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)

print("=" * 68)
print("ENV LOADING DIAGNOSTIC — key value never printed")
print("=" * 68)

# ── 1. Working directory ──────────────────────────────────────────
print(f"\n[1] Backend working directory")
print(f"    cwd: {os.getcwd()}")
print(f"    backend_dir: {backend_dir}")
print(f"    cwd matches backend_dir: {os.getcwd() == backend_dir}")

# ── 2. .env file — raw byte inspection ───────────────────────────
print(f"\n[2] .env file raw inspection")

# Find ALL .env files that might be in scope
for candidate in [
    os.path.join(backend_dir, ".env"),
    os.path.join(backend_dir, "..", ".env"),
    os.path.join(os.getcwd(), ".env"),
]:
    candidate = os.path.normpath(candidate)
    exists = os.path.exists(candidate)
    print(f"    {candidate}")
    print(f"      exists: {exists}")
    if exists:
        with open(candidate, "rb") as f:
            raw = f.read()
        # Check for BOM
        has_bom = raw.startswith(b'\xef\xbb\xbf')
        print(f"      size: {len(raw)} bytes")
        print(f"      BOM (UTF-8 BOM causes parse issues): {has_bom}")
        # Find ELSEVIER line without printing value
        text = raw.decode("utf-8-sig", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("ELSEVIER_API_KEY"):
                # Extract value part safely
                if "=" in stripped:
                    _, _, val = stripped.partition("=")
                    val_stripped = val.strip()
                    # Check for surrounding quotes
                    has_quotes = (
                        (val_stripped.startswith('"') and val_stripped.endswith('"')) or
                        (val_stripped.startswith("'") and val_stripped.endswith("'"))
                    )
                    inner = val_stripped.strip('"\'')
                    length = len(inner)
                    print(f"      Line {lineno}: ELSEVIER_API_KEY=...")
                    print(f"        raw value length (incl. any quotes): {len(val_stripped)}")
                    print(f"        inner length (quotes stripped): {length}")
                    print(f"        has_surrounding_quotes: {has_quotes}")
                    print(f"        starts_with_space: {val.startswith(' ')}")
                    print(f"        ends_with_space: {val.rstrip(chr(13)+chr(10)).endswith(' ')}")
                    # Check for non-printable / unexpected chars (without printing value)
                    non_ascii = [f"0x{ord(c):02x}" for c in inner if ord(c) > 127]
                    print(f"        non-ascii chars: {non_ascii}")
                    print(f"        is_empty: {length == 0}")
                break

# ── 3. OS-level environment override ─────────────────────────────
print(f"\n[3] OS environment override check")
os_val = os.environ.get("ELSEVIER_API_KEY", None)
if os_val is None:
    print("    ELSEVIER_API_KEY: NOT in os.environ (good — .env should win)")
else:
    print(f"    ELSEVIER_API_KEY: PRESENT in os.environ, length={len(os_val)}")
    if len(os_val) == 0:
        print("    *** PROBLEM: os.environ has ELSEVIER_API_KEY='' (empty string)")
        print("    *** pydantic-settings prefers env vars over .env file.")
        print("    *** This empty os.environ value is OVERRIDING the .env value.")
        print("    *** Fix: unset ELSEVIER_API_KEY from the system environment,")
        print("    ***      then restart the backend.")

# ── 4. pydantic-settings load ─────────────────────────────────────
print(f"\n[4] pydantic-settings Settings object")
from app.config import settings
key_len = len(settings.ELSEVIER_API_KEY)
print(f"    settings.ELSEVIER_API_KEY length: {key_len}")
print(f"    settings.ELSEVIER_API_KEY loaded (non-empty): {bool(settings.ELSEVIER_API_KEY)}")
print(f"    settings.INGESTION_ENABLED_SOURCES: {settings.INGESTION_ENABLED_SOURCES}")
print(f"    'elsevier' in enabled_sources: {'elsevier' in settings.enabled_sources_list}")

# ── 5. Connector _is_configured ───────────────────────────────────
print(f"\n[5] ElsevierConnector._is_configured")
from app.services.connectors.elsevier import ElsevierConnector
conn = ElsevierConnector()
print(f"    _api_key length: {len(conn._api_key)}")
print(f"    _is_configured: {conn._is_configured}")

# ── 6. Diagnosis summary ──────────────────────────────────────────
print(f"\n[6] DIAGNOSIS SUMMARY")
if key_len == 0:
    # Was the file value non-empty?
    print("    settings.ELSEVIER_API_KEY is EMPTY after loading.")
    if os_val is not None and len(os_val) == 0:
        print("    CAUSE: os.environ['ELSEVIER_API_KEY'] = '' is overriding .env")
        print("    FIX:   Run:  Remove-Item Env:\\ELSEVIER_API_KEY  (PowerShell)")
        print("           Then restart backend.")
    else:
        print("    CAUSE: Either .env value is truly empty, or has quotes/spaces")
        print("           preventing pydantic-settings from reading it.")
        print("    Check: Does .env line look like:")
        print("           ELSEVIER_API_KEY=abc123   <-- correct")
        print("           ELSEVIER_API_KEY=\"abc123\"  <-- quotes may cause issues")
        print("           ELSEVIER_API_KEY= abc123   <-- leading space wrong")
else:
    print(f"    settings.ELSEVIER_API_KEY is LOADED (length={key_len})")
    print("    Backend has the key. 'Not Configured' must be a RESTART issue.")
    print("    ACTION: The running backend process still has the OLD (empty) value.")
    print("    FIX:    Restart the backend server:")
    print("              Stop uvicorn → start again → re-check Settings page.")

print("\n" + "=" * 68)
