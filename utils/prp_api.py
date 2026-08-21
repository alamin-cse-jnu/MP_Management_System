"""
Shared PRP API plumbing (prp.parliament.gov.bd).

Both PRP integrations use the same two-step auth — POST `…?action=token` for a
Bearer token, then a GET on `/api/secure/external?action=…` with that token in
the Authorization header:

  * apps/mp/management/commands/import_mp_api.py   → action=mpdata_list  (MPs)
  * apps/officer/management/commands/sync_officers.py → action=employeeInformations

Kept here so the token/fetch/credential behaviour stays identical for both.
"""

import json
import os
import urllib.error
import urllib.request

from django.core.management.base import CommandError

BASE_URL = 'https://prp.parliament.gov.bd'
TOKEN_PATH = '/api/authentication/external?action=token'
EMPLOYEE_PATH = '/api/secure/external?action=employeeInformations'


def credentials(username=None, password=None):
    """Resolve API credentials from arguments, falling back to the environment."""
    return (username or os.environ.get('PRP_API_USER'),
            password or os.environ.get('PRP_API_PASS'))


def fetch_json(req, what, timeout=180):
    """Perform an HTTP request and parse JSON, with informative errors."""
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            raw = resp.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as exc:
        body = exc.read().decode('utf-8', 'replace')[:500]
        raise CommandError(f'{what}: HTTP {exc.code} {exc.reason}. Body: {body!r}')
    except urllib.error.URLError as exc:
        raise CommandError(f'{what}: cannot reach server — {exc.reason}')
    if not raw.strip():
        raise CommandError(f'{what}: server returned an EMPTY response '
                           f'(HTTP {status}). Check the URL/credentials.')
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raise CommandError(f'{what}: response was not JSON (HTTP {status}). '
                           f'First 500 chars: {raw[:500]!r}')


def get_token(username, password):
    """Authenticate and return the Bearer token (already prefixed with 'Bearer ')."""
    if not (username and password):
        raise CommandError('PRP API credentials missing — pass --username/--password '
                           'or set env PRP_API_USER / PRP_API_PASS.')
    body = json.dumps({'username': username, 'password': password}).encode('utf-8')
    req = urllib.request.Request(
        BASE_URL + TOKEN_PATH, data=body, method='POST',
        headers={'Content-Type': 'application/json', 'Accept': 'application/json'},
    )
    data = fetch_json(req, 'Token request', timeout=60)
    token = data.get('payload')
    if not token:
        raise CommandError(f'Token request returned no payload: {data}')
    return token


def secure_get(path, token, what, timeout=300):
    """GET an authenticated /api/secure/external endpoint and return parsed JSON."""
    req = urllib.request.Request(BASE_URL + path, headers={
        'Authorization': token,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    })
    return fetch_json(req, what, timeout=timeout)
