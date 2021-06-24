import os
import re
import json
import time
import traceback
import logging
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
from modules.serial_agent import CommandPack


class ApiClient:
    """Api client class that usees an OAuth 2 client session."""

    CACHE_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/../cache"

    def __init__(self, client_id: str, client_secret: str, **kwargs) -> None:
        """Construct a new client.

        Args:
            client_id (str):
            client_secret (str):
            kwargs: Arbitrary keyword arguments.
        """
        self.client_id = client_id
        self.client_secret = client_secret

        self.end_point_token = kwargs.get('end_point_token')
        self.end_point_action = kwargs.get('end_point_action')

        client = BackendApplicationClient(client_id=self.client_id)
        self._oauth2sess = OAuth2Session(client=client)

        self._cache_dir = kwargs.get('cache_dir', self.CACHE_DIR)

    def fetch_token(self, do_cache: bool = True, **kwargs):
        """Request a new client token via the API.

        Args:
            do_cache (bool, optional): Whether to save the obtained token in a file. Defaults to True.
        """
        try:
            res = self._oauth2sess.fetch_token(
                token_url=self.end_point_token,
                client_id=self.client_id,
                client_secret=self.client_secret,
                **kwargs
            )
        except:
            logging.error('Failed to get token (%s)', traceback.format_exc())
            raise
        else:
            if (do_cache):
                self._cache_token(res)

    def get_action(self, **kwargs):
        """Get an action via API.

        If the available token is cached, use it.

        Returns:
            int: The status code of the response.
            CommandPack: The instance of the CommandPack class.
        """

        cached_token = self._get_cached_token()
        logging.debug(cached_token)
        if cached_token:
            self._oauth2sess.token = cached_token

        try:
            url_query = f'{self.end_point_action}/{self.client_id}'
            res = self._oauth2sess.get(url=url_query, **kwargs)
        except:
            logging.error('Failed to get action (%s)', traceback.format_exc())
            raise
        else:
            return res.status_code, CommandPack(res.text)

    def cleanup_cache_dir(self, leave_latest: bool = True):
        """Clean up the directory for storing token files.

        Args:
            leave_latest (bool, optional): [description]. Defaults to True.

        Returns:
            The base name of the latest token cache file.
            Returns 'None' if the file is not found.
        """
        files = os.listdir(self._cache_dir)
        if not files:
            return

        files.sort()

        latest = files.pop(-1)
        expires_at = re.sub('token\.', '', latest)
        if time.time() > float(expires_at) or not leave_latest:
            os.remove(f"{self._cache_dir}/{latest}")
            latest = None

        for cache_file in files:
            os.remove(f"{self._cache_dir}/{cache_file}")

        return latest

    def has_cached_token(self):
        """Checks has the available tokens are cached.

        Returns:
            bool:
        """
        return self._get_cached_token() is not None

    def _cache_token(self, token: dict):
        """Save the specified token dict to a file as a json.

        The format of the file name depends on contents of the token.
        i.e)'token.{access_token}.{espired_at(timestamp)}'

        Args:
            token (dict): The token details, it's have to contains 'access_token' and 'expires_at'.
        """
        if not token.get('access_token') or not token.get('expires_at'):
            logging.warning(f'Invalid parameter! {token!r}')
            return

        self.cleanup_cache_dir(leave_latest=False)

        filepath = f'{self._cache_dir}/token.{token.get("expires_at")}'
        try:
            with open(filepath, 'w') as f:
                json.dump(token, f)
        except:
            logging.error('Failed to create token cache file (%s)',
                          traceback.format_exc())
            raise

    def _get_cached_token(self):
        """Get token details from cached file.

        Returns:
            dict:
        """
        available_cache = self.cleanup_cache_dir()
        if not available_cache:
            return None

        try:
            with open(f"{self._cache_dir}/{available_cache}", 'r') as f:
                token = json.load(f)
        except:
            logging.error('Failed to read token cache file (%s)',
                          traceback.format_exc())
            return None
        else:
            return token

    def __repr__(self) -> str:
        return 'ApiClient'

if __name__ == '__main__':
    pass
