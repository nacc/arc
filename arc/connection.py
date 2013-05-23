"""
This module provides connection classes to both the AFE and TKO services of the
autotest server.

A connection is a simple wrapper around a JSON-RPC Proxy instance. It is the
basic object that allows methods to be called on the remote RPC server.
"""


__all__ = ['get_default', 'Connection', 'AfeConnection', 'TkoConnection']


import os

import arc.config
import arc.defaults
import arc.jsonrpc


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


class InvalidProxyError(Exception):
    """
    Invalid proxy for selected service
    """
    pass


class BaseConnection(object):
    """
    Base RPC connection
    """
    def __init__(self, hostname=None, port=None, path=None):
        """
        Initializes a connection to an empty path

        This empty path does not exist on a default Autotest server
        """
        if hostname is None:
            hostname = arc.config.get_default().get_server_host()
        self.hostname = hostname

        if port is None:
            port = arc.config.get_default().get_server_port()
        self.port = port

        if path is None:
            path = arc.defaults.RPC_PATH

        self.services = {}
        self.service_proxies = {}
        self.service_interface_versions = {}

        try:
            self.proxy = self._connect(path)
        except RpcAuthError:
            raise AuthError


    def _connect(self, path):
        """
        Setup authorization headers and instantiate a JSON RPC Service Proxy

        :param path: the URI path where the service is hosted
        """
        headers = {'AUTHORIZATION': os.environ.get('USER', 'debug_user')}
        rpc_uri = "http://%s:%s%s" % (self.hostname, self.port, path)
        return arc.jsonrpc.ServiceProxy(rpc_uri, headers=headers)


    def run(self, service, operation, *args, **data):
        """
        Runs a method using the rpc proxy

        This method is heavily used by upper level API methods, and more often
        than not, those upper level API methods should be used instead.

        :param operation: the name of the RPC method on the Autotest server
        :param args: positional arguments to be passed to the RPC method
        :param data: keyword arguments to be passed to the RPC method
        """
        proxy = self.service_proxies.get(service, None)
        if proxy is None:
            raise InvalidProxyError

        function = getattr(proxy, operation)
        result = function(*args, **data)
        return result


    def add_service(self, name, path):
        """
        Add a service to a connection

        :param name: a descriptive name to the service
        :param path: the path in the URI that hosts the service
        """
        self.services[name] = path
        self.service_proxies[name] = self._connect(path)
        try:
            api_version = self.run(name, "get_interface_version")
        except:
            api_version = None
        self.service_interface_versions[name] = api_version


    def ping(self):
        """
        Tests connectivity to the RPC server
        """
        try:
            result = self.run(arc.defaults.AFE_SERVICE_NAME, "get_server_time")
        except:
            return False
        return True


class Connection(BaseConnection):
    """
    The default connection that allows access to both AFE and TKO services

    :param hostname: the IP address or hostname of the server that will be
           contacted upon RPC method execution.
    """
    def __init__(self, hostname=None, port=None):
        super(Connection, self).__init__(hostname, port)
        self.add_service(arc.defaults.AFE_SERVICE_NAME,
                         arc.defaults.AFE_RPC_PATH)
        self.add_service(arc.defaults.TKO_SERVICE_NAME,
                         arc.defaults.TKO_RPC_PATH)


#: Global, default connection to an AFE service for ease of use by apps
CONNECTION = None


def get_default():
    """
    Returns the global, default connection to an AFE service

    :returns: an arc.connection.AfeConnection instance
    """
    global CONNECTION

    if CONNECTION is None:
       CONNECTION = Connection()

    return CONNECTION
