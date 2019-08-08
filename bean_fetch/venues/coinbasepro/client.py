import hmac
import hashlib
import time
import requests
import base64
import json
from typing import Dict, Mapping, Any, List, Optional, Generator

from requests.auth import AuthBase

from .data import Product


class CBProAuth(AuthBase):
    # Provided by CBPro: https://docs.pro.coinbase.com/#signing-a-message
    def __init__(self, api_key: str, secret_key: str, passphrase: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request: requests.PreparedRequest) -> requests.PreparedRequest:
        timestamp = str(time.time())
        message = "".join(
            [timestamp, (request.method or ""), request.path_url, (request.body or "")]
        )
        request.headers.update(
            get_auth_headers(
                timestamp, message, self.api_key, self.secret_key, self.passphrase
            )
        )
        return request


def get_auth_headers(
    timestamp: str, message: str, api_key: str, secret_key: str, passphrase: str
) -> Dict[str, Any]:
    encoded = message.encode("ascii")
    hmac_key = base64.b64decode(secret_key)
    signature = hmac.new(hmac_key, encoded, hashlib.sha256)
    signature_b64 = base64.b64encode(signature.digest()).decode("utf-8")
    return {
        "Content-Type": "Application/JSON",
        "CB-ACCESS-SIGN": signature_b64,
        "CB-ACCESS-TIMESTAMP": timestamp,
        "CB-ACCESS-KEY": api_key,
        "CB-ACCESS-PASSPHRASE": passphrase,
    }


class Client:
    def __init__(
        self,
        key: str,
        b64secret: str,
        passphrase: str,
        api_url: str = "https://api.pro.coinbase.com",
    ):
        self.url = api_url.rstrip("/")
        self.auth = CBProAuth(key, b64secret, passphrase)
        self.session = requests.Session()

    def get_products(self) -> Any:
        return self._send_message("get", "/products")

    def get_accounts(self) -> Any:
        return self._send_message("get", "/accounts/")

    def get_fills(
        self,
        product_id: Optional[str] = None,
        order_id: Optional[str] = None,
        **kwargs: Any
    ) -> Any:
        if (product_id is None) and (order_id is None):
            raise ValueError("Either product_id or order_id must be specified.")

        params = {}
        if product_id:
            params["product_id"] = product_id
        if order_id:
            params["order_id"] = order_id
        params.update(kwargs)

        return self._send_paginated_message("/fills", params=params)

    def get_account_history(self, account_id: str, **kwargs: Any) -> Any:
        endpoint = "/accounts/{}/ledger".format(account_id)
        return self._send_paginated_message(endpoint, params=kwargs)

    def _send_message(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[Any, Any]] = None,
        data: Optional[bytes] = None,
    ) -> Any:
        url = self.url + endpoint
        r = self.session.request(
            method, url, params=params, data=data, auth=self.auth, timeout=30
        )
        return r.json()

    def _send_paginated_message(
        self, endpoint: str, params: Optional[Dict[Any, Any]] = None
    ) -> Generator[Any, None, None]:
        if params is None:
            params = dict()
        url = self.url + endpoint
        while True:
            r = self.session.get(url, params=params, auth=self.auth, timeout=30)
            results = r.json()
            for result in results:
                yield result
            # If there are no more pages, we're done. Otherwise update `after`
            # param to get next page.
            # If this request included `before` don't get any more pages - the
            # cbpro API doesn't support multiple pages in that case.
            if not r.headers.get("cb-after") or params.get("before") is not None:
                break
            else:
                params["after"] = r.headers["cb-after"]
