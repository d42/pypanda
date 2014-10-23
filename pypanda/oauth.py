import time
import hmac
import base64
import random
import urllib.parse

from urllib.parse import quote
from collections import OrderedDict
from hashlib import md5, sha1

class OAuth:
    auth_token = ""
    auth_secret = ""
    consumer_key = "53howg62v4ow80ck8ws4wwowos4ock40w4o0ssgoowss88so4g"
    consumer_secret = "2gf7bsrw3x34w8ogwko0o00044gggkwk80o0c4w000o4kskc4w"

    def get_nonce(self, param=''):
        string = ''.join([param, self.consumer_key, time.strftime('%s'), str(random.random())])
        return md5(string.encode('utf-8')).hexdigest()

    def get_signature(self, base_url, param_dict, request_type='POST'):
        key = '&'
        key= (quote(self.consumer_secret, safe='') + '&' + quote(self.auth_secret, safe='')).encode('utf-8')

        params = '&'.join('{}={}'.format(k, v)
                          for k, v in sorted(param_dict.items()))
        params = quote(params, safe='')

        message = (request_type + '&' + quote(base_url, safe='') + '&' + params).encode('utf-8')

        signature = hmac.HMAC(key, message, digestmod=sha1).hexdigest()
        b64signature = base64.b64encode(signature.encode('utf-8')).strip()
        return b64signature

    def set_token(self, token, secret):
        self.auth_token = token
        self.auth_secret = secret

    @property
    def setup(self):
        return self.auth_token and self.auth_secret

    def oauth_data(self, url, params=None, request_type='POST'):
        nonce = self.get_nonce()
        timestamp = time.strftime('%s')

        auth_params = OrderedDict([
            ("oauth_consumer_key", self.consumer_key),
            ("oauth_timestamp", time.strftime('%s')),
            ("oauth_signature_method", 'HMAC-SHA1'),
            ("oauth_nonce", nonce)
        ])

        if self.auth_token:
            auth_params['oauth_token'] = quote(self.auth_token)

        signature_params = OrderedDict()
        signature_params.update(auth_params)

        if params:
            signature_params.update(params)

        signature = self.get_signature(url, signature_params, request_type)
        auth_params.update({"oauth_signature": quote(signature, safe='')})

        return auth_params


