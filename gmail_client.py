# gmail_oauth.py
import requests
from urllib.parse import urlencode
from typing import Dict, Any, Optional
from oath2_interface import BaseOAuthProvider, OAuthConfig


class GmailOAuthProvider(BaseOAuthProvider):
    """Gmail OAuth 2.0  implementation"""

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """生成 Gmail 授權 URL"""
        params = {
            'client_id': self.config.client_id,
            'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
            'scope': ' '.join(self.config.scopes),
            'response_type': 'code',
            'access_type': 'offline',  # 為了取得 refresh_token
            'prompt': 'consent'  # 強制顯示同意畫面
        }

        if state:
            params['state'] = state

        return f"{self.config.auth_url}?{urlencode(params)}"

    def get_tokens(self, authorization_code: str) -> Dict[str, Any]:
        """用授權碼換取 Gmail tokens"""
        data = {
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret,
            'code': authorization_code,
            'grant_type': 'authorization_code',
            'redirect_uri': self.config.redirect_uri
        }

        try:
            response = requests.post(self.config.token_url, data=data)
            response.raise_for_status()
            self.token_data = response.json()
            return self.token_data
        except requests.exceptions.RequestException as e:
            print(f"❌ 取得 tokens 失敗: {e}")
            raise

    def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """刷新 Gmail access token"""
        data = {
            'client_id': self.config.client_id,
            'client_secret': self.config.client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token'
        }

        try:
            response = requests.post(self.config.token_url, data=data)
            response.raise_for_status()
            new_tokens = response.json()

            # 更新 token_data，保留原有的 refresh_token
            if self.token_data:
                self.token_data.update(new_tokens)
            else:
                self.token_data = new_tokens
                self.token_data['refresh_token'] = refresh_token

            return self.token_data
        except requests.exceptions.RequestException as e:
            print(f"❌ 刷新 tokens 失敗: {e}")
            raise

    def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """取得 Gmail 使用者資訊"""
        headers = {'Authorization': f'Bearer {access_token}'}
        url = f'{self.config.api_base_url}/oauth2/v2/userinfo'

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ 取得使用者資訊失敗: {e}")
            raise

    def revoke_tokens(self, token: str) -> bool:
        """撤銷 Gmail tokens"""
        revoke_url = 'https://oauth2.googleapis.com/revoke'
        data = {'token': token}

        try:
            response = requests.post(revoke_url, data=data)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False