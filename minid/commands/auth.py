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
from __future__ import print_function
import logging

from minid.commands.argparse_ext import subcommand, argument
from minid.commands.cli import subparsers
from minid.exc import TokensExpired
import minid.auth
from minid.config import config

log = logging.getLogger(__name__)


@subcommand(
    [
        argument(
            '--remember-me',
            action='store_true',
            default=False,
            help='Ask for a refresh token to prolong login time'),
        argument(
            '--force',
            action='store_true',
            default=False,
            help='Do a fresh login, ignoring any existing credentials'),
        argument(
            "--no-local-server",
            action='store_true',
            default=False,
            help='Manual login by copying and pasting an auth code.'),
        argument(
            "--no-browser",
            action='store_true',
            default=False,
            help='Do not automatically open the browser to login'),
    ],
    parent=subparsers,
    help='Login to register Minids',
)
def login(minid_client, args):
    try:
        if not args.force:
            if config.load_tokens():
                log.info('You are already logged in.')
                return
    except TokensExpired:
        log.debug('Tokens expired, proceeding to login...')
    except Exception as e:
        log.debug('Loading tokens failed, proceeding to login...')

    tokens = minid.auth.login(refresh_tokens=args.remember_me,
                              no_local_server=args.no_local_server,
                              no_browser=args.no_browser)
    config.save_tokens(tokens)
    log.info('You have been logged in.')


@subcommand([], parent=subparsers, help='Logout to clear stored credentials')
def logout(minid_client, args):
    tokens = config.load_tokens()
    if tokens:
        minid.auth.logout(config.load_tokens())
        config.remove_section('tokens')
        config.add_section('tokens')
        config.save()
        log.info('You have been logged out.')
    else:
        log.info('No user logged in, no logout necessary.')
