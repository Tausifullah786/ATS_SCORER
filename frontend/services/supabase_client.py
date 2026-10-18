import os
import logging
from pathlib import Path
from typing import Any, Dict
import streamlit as st
from supabase import Client, create_client

logger = logging.getLogger('ats_resume_scorer')


try:
    from dotenv import load_dotenv
    # Match the backend's configuration paths, regardless of launch directory.
    # Process env and project-root values take precedence over backend/.env.
    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    load_dotenv(_PROJECT_ROOT / '.env', override=False)
    load_dotenv(_PROJECT_ROOT / 'backend' / '.env', override=False)
except ImportError:
    pass


def _secret(key: str, section: str = 'supabase') -> str:
    """Read from env first, then fall back to st.secrets[section][key]."""
    val = os.getenv(key, '')
    if val:
        return val
    try:
        return st.secrets[section][key]
    except (KeyError, FileNotFoundError, AttributeError):
        return ''


SUPABASE_URL = _secret('SUPABASE_URL')
SUPABASE_ANON_KEY = _secret('SUPABASE_ANON_KEY')

OAUTH_REDIRECT_URL = (
    os.getenv('AUTH_REDIRECT_URL')
    or _secret('redirect_uri', 'google_oauth')
    or 'http://localhost:8501'
)


def _missing_config() -> str | None:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return 'Supabase is not configured — set SUPABASE_URL and SUPABASE_ANON_KEY in backend/.env, .env, or .streamlit/secrets.toml'
    return None


@st.cache_resource
def get_client() -> Client | None:
    """Cached singleton — preserves PKCE state across Streamlit reruns."""
    if _missing_config():
        return None
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def _session_dict(session, user) -> Dict[str, Any]:
    return {
        'access_token':  session.access_token,
        'refresh_token': session.refresh_token,
        'user_id':       user.id,
        'email':         user.email,
    }


def sign_in_with_password(email: str, password: str) -> Dict[str, Any]:
    email = email.strip()
    if not email or not password:
        return {'error': 'Enter your email address and password.'}
    err = _missing_config()
    if err:
        return {'error': err}
    try:
        resp = get_client().auth.sign_in_with_password(
            {'email': email, 'password': password}
        )
        if not resp.session or not resp.user:
            return {'error': 'Sign-in did not return a session. Please try again.'}
        return _session_dict(resp.session, resp.user)
    except Exception as exc:
        logger.warning(f'sign_in_with_password failed: {exc}')
        return {'error': _humanize(exc)}


def sign_up_with_password(email: str, password: str) -> Dict[str, Any]:
    email = email.strip()
    if not email or not password:
        return {'error': 'Enter your email address and password.'}
    err = _missing_config()
    if err:
        return {'error': err}
    try:
        resp = get_client().auth.sign_up({'email': email, 'password': password})
        if resp.session and resp.user:
            return _session_dict(resp.session, resp.user)
        if resp.user:
            return {'pending_confirmation': True, 'email': email}
        return {'error': 'Sign-up failed'}
    except Exception as exc:
        logger.warning(f'sign_up failed: {exc}')
        return {'error': _humanize(exc)}


def google_oauth_url() -> Dict[str, Any]:
    err = _missing_config()
    if err:
        return {'error': err}
    try:
        resp = get_client().auth.sign_in_with_oauth({
            'provider': 'google',
            'options': {'redirect_to': OAUTH_REDIRECT_URL},
        })
        return {'url': resp.url}
    except Exception as exc:
        logger.warning(f'oauth url generation failed: {exc}')
        return {'error': _humanize(exc)}


def exchange_code_for_session(auth_code: str) -> Dict[str, Any]:
    """Called once after the OAuth provider redirects back with `?code=...`."""
    err = _missing_config()
    if err:
        return {'error': err}
    client = get_client()
    try:
        storage_key = f'{client.auth._storage_key}-code-verifier'
        code_verifier = client.auth._storage.get_item(storage_key) or ''
        resp = client.auth.exchange_code_for_session({
            'auth_code': auth_code,
            'code_verifier': code_verifier,
            'redirect_to': OAUTH_REDIRECT_URL,
        })
        if not resp.session or not resp.user:
            return {'error': 'OAuth exchange returned no session'}
        return _session_dict(resp.session, resp.user)
    except Exception as exc:
        logger.warning(f'exchange_code_for_session failed: {exc}')
        return {'error': _humanize(exc)}


def sign_out() -> None:
    if _missing_config():
        return
    try:
        get_client().auth.sign_out()
    except Exception as exc:
        logger.warning(f'sign_out failed: {exc}')


def _humanize(exc: Exception) -> str:
    msg = str(exc)
    code = getattr(exc, 'code', None)
    lower_msg = msg.lower()
    if code == 'email_not_confirmed' or 'email not confirmed' in lower_msg:
        return 'Confirm your email using the link in your inbox (or spam folder), then sign in.'
    if code == 'invalid_credentials' or 'invalid login' in lower_msg:
        return (
            'Supabase could not sign you in with that email and password. '
            'Use the credentials from your original sign-up; signing up again '
            'does not reset an existing account password.'
        )
    if code in ('over_email_send_rate_limit', 'over_request_rate_limit'):
        return 'Too many authentication requests. Wait before trying again and check your inbox for an earlier email.'
    if code == 'email_address_not_authorized':
        return 'Email delivery is restricted for this Supabase project. The project owner needs to configure SMTP to send to this address.'
    if code == 'signup_disabled':
        return 'New account registration is disabled for this Supabase project.'
    if code == 'email_provider_disabled':
        return 'Email/password authentication is disabled for this Supabase project.'
    if code == 'user_already_exists' or 'user already registered' in lower_msg or 'already been registered' in lower_msg:
        return 'An account with this email already exists — try signing in'
    if code == 'weak_password' or 'password should be at least' in lower_msg:
        return f'Password does not meet this project\'s requirements: {msg}'
    return msg
