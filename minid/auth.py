"""
Copyright 2016 University of Chicago, University of Southern California

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import logging
from native_login import NativeClient


log = logging.getLogger(__name__)

# The Minid Client ID needs to be added to the identifiers whitelist
# CLIENT_ID = 'aa334131-1b9c-44e4-b9ff-ee1600863128'
CLIENT_ID = 'b61613f8-0da8-4be7-81aa-1c89f2c0fe9f'
SCOPES = ('https://auth.globus.org/scopes/'
          'identifiers.globus.org/create_update',)

client = NativeClient(client_id=CLIENT_ID,
                      app_name='Minid Client',
                      token_storage=None)


def login(refresh_tokens=False, no_local_server=False, no_browser=False):
    return client.login(requested_scopes=SCOPES,
                        refresh_tokens=refresh_tokens,
                        no_local_server=no_local_server,
                        no_browser=no_browser
                        )


def logout(tokens):
    """
    Revokes tokens in the same format received from login()

    {"identifiers.globus.org": {
        "access_token": "my_access_token",
        "refresh_token": "my_refresh_token",
        ...
        }
    }
    Example:
        tokens = login()
        logout(tokens)
    """
    client.revoke_token_set(tokens)