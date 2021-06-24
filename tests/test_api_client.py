import base64
import json
import time
import datetime
import os
from pathlib import Path
from random import randint
import unittest
import requests
from oauthlib.oauth2.rfc6749.errors import MissingTokenError, TokenExpiredError
import requests_mock

from tests.context import *
from modules.api_client import ApiClient
from modules.serial_agent import CommandPack


class TestApiClient(unittest.TestCase):

    TEST_CACHE_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/tmp"

    TEST_API_SETTINGS = {
        'client_id': 'dummyclientid',
        'client_secret': 'client_secret_zzzzzzzzzzzzzz',
        'end_point_token': 'https://localhost:8000/robots/connect',
        'end_point_action': 'https://localhost:3000/action',
        'cache_dir': TEST_CACHE_DIR
    }

    LOCAL_API_SETTINGS = {
        'client_id': 'w4aLasXfQznyYNhgW4kgieRgjJPUPvWifOGa5kbq',
        'client_secret': 'brRvVn2CChPi0pYftTFsulWTKhjDLv3TUUspqSXQwrz2YIld9Hbj1YGDQfiGe2RIHKkawVjUSUWB1Qbx0NxN9bVaZDFeqw8jP1LeNbaOeJUWj4P8rPx68BdkCltsLozh',
        'end_point_token': 'https://automata.local/robots/connect/',
        'end_point_action': 'https://heartbeat.local/action',
        'cache_dir': TEST_CACHE_DIR
    }

    MOCK_TOKEN_RESPONSE = {
        #'access_token': base64.b64encode('dummytoken'.encode('utf-8')).decode('utf-8'),
        'access_token': 'dummytoken',
        'token_type': 'bearer',
        'expires_in': 3600,
        'scope': 'breathing'
    }

    @classmethod
    def setUpClass(cls) -> None:
        init_test_logger()

        TestApiClient.SKIP_SYSTEM_TEST = not has_active_devenv()

        return super().setUpClass()

    def tearDown(self) -> None:
        # clear tmp directory
        for file in os.listdir(self.TEST_CACHE_DIR):
            os.remove(f'{self.TEST_CACHE_DIR}/{file}')

        return super().tearDown()

    def _get_authorized_client(self, **response_token):
        # Merge response token mock
        res_token = {}
        for key, val in self.MOCK_TOKEN_RESPONSE.items():
            res_token[key] = response_token.get(key, val)

        with requests_mock.Mocker() as req_mock:
            req_mock.post(self.TEST_API_SETTINGS.get(
                'end_point_token'), json=res_token)
            client = ApiClient(**self.TEST_API_SETTINGS)
            client.fetch_token()

        return client

    def _generate_token_cache_mock(self, amount=3, time_range_from=10, time_rang_to=3600):
        for i in range(amount):
            dummy_date = datetime.datetime.now(
            ) + datetime.timedelta(seconds=randint(time_range_from, time_rang_to))
            with open(f"{self.TEST_CACHE_DIR}/token.{dummy_date.timestamp()}", 'w') as f:
                json.dump(self.MOCK_TOKEN_RESPONSE, f)

            # Note: create empty file example
            # Path(f"{self.TEST_CACHE_DIR}/token.{dummy_date.timestamp()}").touch()

        return [os.path.basename(x) for x in os.listdir(self.TEST_CACHE_DIR)]

    def _make_api_action_url(self):
        return f"{self.TEST_API_SETTINGS['end_point_action']}/{self.TEST_API_SETTINGS['client_id']}"

    def test_create_instance(self):
        client = ApiClient(**self.TEST_API_SETTINGS)
        self.assertIsInstance(client, ApiClient)

    @requests_mock.Mocker()
    def test_fetch_token(self, req_mock):
        req_mock.post(self.TEST_API_SETTINGS.get(
            'end_point_token'), json=self.MOCK_TOKEN_RESPONSE)
        client = ApiClient(**self.TEST_API_SETTINGS)
        client.fetch_token()

    @requests_mock.Mocker()
    def test_get_action(self, req_mock):
        client = self._get_authorized_client()
        req_mock.get(self._make_api_action_url(), json={})
        status, res = client.get_action()

        self.assertEqual(status, 200)
        self.assertIsInstance(res, CommandPack)
        self.assertTrue(len(res.items) == 0)

    @requests_mock.Mocker()
    def test_get_action_with_expired_token(self, req_mock):
        client = self._get_authorized_client(**{'expires_in': 1})
        req_mock.get(self._make_api_action_url(), json={})

        time.sleep(1)
        with self.assertRaises(TokenExpiredError):
            client.get_action()

    @requests_mock.Mocker()
    def test_get_action_use_cached_token(self, req_mock):
        client1 = self._get_authorized_client(**{'scope': 'pee'})

        req_mock.get(self._make_api_action_url(), json={})
        req_mock.post(self.TEST_API_SETTINGS.get(
            'end_point_token'), json=self.MOCK_TOKEN_RESPONSE)

        client2 = ApiClient(**self.TEST_API_SETTINGS)
        client2.fetch_token(do_cache=False)

        client2.get_action()
        self.assertEqual(client2._oauth2sess.token, client1._oauth2sess.token)

    def test_cleanup_cache_all(self):
        client = ApiClient(**self.TEST_API_SETTINGS)
        client.cleanup_cache_dir(leave_latest=False)

        dummy_files = self._generate_token_cache_mock(amount=3)
        self.assertTrue(len(dummy_files) == 3)

        client.cleanup_cache_dir(leave_latest=False)
        self.assertTrue(len(os.listdir(self.TEST_CACHE_DIR)) == 0)

    def test_cleanup_cache_leave_latest(self):
        client = ApiClient(**self.TEST_API_SETTINGS)
        client.cleanup_cache_dir(leave_latest=False)

        dummy_files = self._generate_token_cache_mock(amount=3)
        self.assertTrue(len(dummy_files) == 3)
        dummy_files.sort()

        latest = client.cleanup_cache_dir(leave_latest=True)
        self.assertEqual(dummy_files.pop(-1), os.path.basename(latest))

    def test_cleanup_cache_leave_latest_but_expired(self):
        client = ApiClient(**self.TEST_API_SETTINGS)
        client.cleanup_cache_dir(leave_latest=False)

        dummy_files = self._generate_token_cache_mock(
            amount=3, time_range_from=-3600, time_rang_to=0)
        self.assertTrue(len(dummy_files) == 3)

        client.cleanup_cache_dir(leave_latest=True)
        self.assertTrue(len(os.listdir(self.TEST_CACHE_DIR)) == 0)

    def test_fetch_token_use_external_end_point(self):
        if TestApiClient.SKIP_SYSTEM_TEST:
            self.skipTest('This test require active api server.')
            return
        
        client = ApiClient(**self.LOCAL_API_SETTINGS)

        # **Only for local self-signed certificate**
        client.fetch_token(**{'verify': False})

        cached = os.listdir(self.TEST_CACHE_DIR)
        self.assertEqual(len(cached), 1)
        with open(f'{self.TEST_CACHE_DIR}/{cached[0]}', 'r') as token_cache:
            logging.debug(token_cache.readlines())

    def test_get_action_use_external_end_point(self):
        if TestApiClient.SKIP_SYSTEM_TEST:
            self.skipTest('This test require active api server.')
            return

        client = self._get_authorized_client()
        client.end_point_action = self.LOCAL_API_SETTINGS['end_point_action']

        # **Only for local self-signed certificate**
        status, res = client.get_action(**{'verify': False})

        self.assertEqual(status, 200)
        self.assertIsInstance(res, CommandPack)
        #print(res.items)

    def test_workflow_fetch_and_get_action(self):
        if TestApiClient.SKIP_SYSTEM_TEST:
            self.skipTest('This test require active api server.')
            return

        client = ApiClient(**self.LOCAL_API_SETTINGS)
        
        # **Only for local self-signed certificate**
        client.fetch_token(**{'verify': False})
        status, res = client.get_action(**{'verify': False})

        self.assertEqual(status, 200)
        self.assertIsInstance(res, CommandPack)
        #print(res.items)



