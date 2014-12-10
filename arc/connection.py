# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
# Copyright (c) 2013-2015 Red Hat
# Author: Cleber Rosa <cleber@redhat.com>

"""
This module provides connection classes the avocado server.

A connection is a simple wrapper around a HTTP request instance. It is this
basic object that allows methods to be called on the remote server.
"""

import arc.config

import requests


__all__ = ['get_default', 'Connection']


#: Minimum required version of server side API
MIN_REQUIRED_VERSION = (0, 1, 0)


class AuthError(Exception):

    """
    Authentication Error reported users of the connection module
    """
    pass


class RpcAuthError(Exception):

    """
    Internal (between connection and Rpc Proxy) Authentication Error
    """
    pass


class InvalidConnectionError(Exception):

    """
    Invalid connection for selected server
    """
    pass


class InvalidServerVersionError(Exception):

    """
    The server version does not satisfy the minimum required version
    """
    pass


class Connection(object):

    """
    Connection to the avocado server
    """

    def __init__(self, hostname=None, port=None, username=None, password=None):
        """
        Initializes a connection to an avocado server instance

        :param hostname:
        :type hostname:
        :param port:
        :type port:
        :param username:
        :type username:
        :param password:
        :type password:
        """
        if hostname is None:
            hostname = arc.config.get_default().get_server_host()
        self.hostname = hostname

        if port is None:
            port = arc.config.get_default().get_server_port()
        self.port = port

        if username is None:
            username = arc.config.get_default().get_username()
        self.username = username

        self.password = password

        try:
            min_version_ok = self.check_min_version()
            if not min_version_ok:
                raise InvalidServerVersionError
            pass
        except RpcAuthError:
            raise AuthError

    def get_url(self, path):
        return 'http://%s:%s/%s' % (self.hostname, self.port, path)

    def run(self, path, method=requests.get, **data):
        """
        Runs a method using the rpc proxy

        This method is heavily used by upper level API methods, and more often
        than not, those upper level API methods should be used instead.

        :param operation: the name of the RPC method on the Autotest server
        :param method: the method you want to call on the remote server,
                       defaults to a HTTP GET
        :param data: keyword arguments to be passed to the remote method
        """
        url = self.get_url(path)

        if (self.username is not None) and (self.password is not None):
            return method(url,
                          auth=(self.username, self.password),
                          params=data)
        else:
            return method(url, params=data)

    def check_min_version(self):
        """
        Checks the minimum server version
        """
        response = self.run('version')
        version = response.json().get('version')
        if version is None:
            return False

        major, minor, release = version.split('.', 3)
        version = (int(major), int(minor), int(release))
        return version >= MIN_REQUIRED_VERSION

    def ping(self):
        """
        Tests connectivity to the RPC server
        """
        try:
            self.run('version')
        except:
            return False
        return True


#: Global, default connection for ease of use by apps
CONNECTION = None


def get_default():
    """
    Returns the global, default connection to an AFE service

    :returns: an arc.connection.Connection instance
    """
    global CONNECTION

    if CONNECTION is None:
        CONNECTION = Connection()

    return CONNECTION
