import time
import unittest
from unittest.mock import patch

import jwt
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from backend.api import auth
from backend.main import app as main_app


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.secret = 'test-only-signing-secret-at-least-32-bytes'
        self.config = patch.multiple(
            auth, SUPABASE_URL='', SUPABASE_JWT_SECRET=self.secret
        )
        self.config.start()
        self.addCleanup(self.config.stop)
        app = FastAPI()

        @app.get('/protected')
        def protected(user_id: str = Depends(auth.get_current_user)):
            return {'user_id': user_id}

        self.client = TestClient(app)
        self.addCleanup(self.client.close)

    def token(self, **overrides):
        claims = {'sub': 'test-user', 'aud': 'authenticated', 'exp': time.time() + 60}
        claims.update(overrides)
        return jwt.encode(claims, self.secret, algorithm='HS256')

    def request(self, token):
        return self.client.get('/protected', headers={'Authorization': f'Bearer {token}'})

    def test_missing_token_has_swagger_instructions(self):
        response = self.client.get('/protected')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers['www-authenticate'], 'Bearer')
        self.assertIn('Authorize', response.json()['detail'])

    def test_valid_user_token_is_accepted(self):
        response = self.request(self.token())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'user_id': 'test-user'})

    def test_invalid_token_is_rejected(self):
        self.assertEqual(self.request('not-a-jwt').status_code, 401)

    def test_expired_token_is_rejected(self):
        self.assertEqual(self.request(self.token(exp=time.time() - 60)).status_code, 401)

    def test_wrong_audience_is_rejected(self):
        self.assertEqual(self.request(self.token(aud='anon')).status_code, 401)

    def test_missing_subject_is_rejected(self):
        self.assertEqual(self.request(self.token(sub='')).status_code, 401)

    def test_swagger_exposes_bearer_auth_and_401(self):
        schema = main_app.openapi()
        scheme = schema['components']['securitySchemes']['HTTPBearer']
        self.assertEqual(scheme['scheme'], 'bearer')
        self.assertIn('access_token', scheme['description'])
        operation = schema['paths']['/api/v1/analyze-resume']['post']
        self.assertEqual(operation['security'], [{'HTTPBearer': []}])
        self.assertIn('401', operation['responses'])


if __name__ == '__main__':
    unittest.main()
