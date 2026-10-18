import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from frontend.services import supabase_client as auth


class AuthError(Exception):
    def __init__(self, message, code):
        super().__init__(message)
        self.code = code


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        for mocked in (
            patch.object(auth, 'get_client', return_value=self.client),
            patch.object(auth, '_missing_config', return_value=None),
            patch.object(auth, 'logger'),
        ):
            mocked.start()
            self.addCleanup(mocked.stop)

    def test_signin_trims_email_but_preserves_password(self):
        self.client.auth.sign_in_with_password.return_value = SimpleNamespace(
            user=SimpleNamespace(id='user-id', email='user@example.com'),
            session=SimpleNamespace(access_token='test-access', refresh_token='test-refresh'),
        )
        result = auth.sign_in_with_password(' user@example.com ', ' password ')
        self.client.auth.sign_in_with_password.assert_called_once_with(
            {'email': 'user@example.com', 'password': ' password '}
        )
        self.assertEqual(result['user_id'], 'user-id')

    def test_signup_without_session_requires_confirmation(self):
        self.client.auth.sign_up.return_value = SimpleNamespace(
            user=SimpleNamespace(id='user-id'), session=None
        )
        result = auth.sign_up_with_password(' user@example.com ', ' password ')
        self.assertEqual(result, {'pending_confirmation': True, 'email': 'user@example.com'})
        self.client.auth.sign_up.assert_called_once_with(
            {'email': 'user@example.com', 'password': ' password '}
        )

    def test_blank_credentials_do_not_contact_supabase(self):
        for operation in (auth.sign_in_with_password, auth.sign_up_with_password):
            for email, password in ((' ', 'password'), ('user@example.com', '')):
                self.assertIn('error', operation(email, password))
        self.client.auth.sign_in_with_password.assert_not_called()
        self.client.auth.sign_up.assert_not_called()

    def test_unconfirmed_email_has_confirmation_instructions(self):
        self.client.auth.sign_in_with_password.side_effect = AuthError(
            'Email not confirmed', 'email_not_confirmed'
        )
        result = auth.sign_in_with_password('user@example.com', 'password')
        self.assertIn('Confirm your email', result['error'])
        self.assertNotIn('password', result['error'])

    def test_invalid_credentials_explains_repeat_signup(self):
        self.client.auth.sign_in_with_password.side_effect = AuthError(
            'Invalid login credentials', 'invalid_credentials'
        )
        result = auth.sign_in_with_password('user@example.com', 'password')
        self.assertIn('does not reset', result['error'])

    def test_email_delivery_errors_are_not_password_errors(self):
        for code, expected in (
            ('over_email_send_rate_limit', 'Wait'),
            ('email_address_not_authorized', 'SMTP'),
            ('signup_disabled', 'registration is disabled'),
        ):
            with self.subTest(code=code):
                self.client.auth.sign_up.side_effect = AuthError('Request rejected', code)
                result = auth.sign_up_with_password('user@example.com', 'password')
                self.assertIn(expected, result['error'])

    def test_missing_session_is_not_misreported_as_bad_password(self):
        self.client.auth.sign_in_with_password.return_value = SimpleNamespace(
            user=None, session=None
        )
        result = auth.sign_in_with_password('user@example.com', 'password')
        self.assertIn('did not return a session', result['error'])

    def test_unrelated_invalid_grant_is_not_misreported_as_bad_password(self):
        self.assertEqual(auth._humanize(Exception('invalid_grant: expired code')),
                         'invalid_grant: expired code')


if __name__ == '__main__':
    unittest.main()
