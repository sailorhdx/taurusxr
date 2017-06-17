# coding: utf-8
#
# Copyright 2010 Alexandre Fiori
# based on the original Tornado by Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Non-blocking HTTP client"""

import functools
import types

from cyclone import escape
from cyclone.web import HTTPError

from twisted.internet import defer
from twisted.internet import reactor
from twisted.internet.protocol import Protocol

from twisted.web.client import Agent
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer

from zope.interface import implements

agent = Agent(reactor)


class StringProducer(object):
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return defer.succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


class Receiver(Protocol):
    def __init__(self, finished):
        self.finished = finished
        self.data = []

    def dataReceived(self, bytes):
        self.data.append(bytes)

    def connectionLost(self, reason):
        self.finished.callback("".join(self.data))


class HTTPClient(object):
    def __init__(self, url, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self.url = url
        self.followRedirect = self._kwargs.get("followRedirect", 0)
        self.maxRedirects = self._kwargs.get("maxRedirects", 3)
        self.headers = self._kwargs.get("headers", {})
        self.body = self._kwargs.get("postdata")
        self.method = self._kwargs.get("method", self.body and "POST" or "GET")
        agent._connectTimeout = self._kwargs.get("timeout", None)
        if self.method.upper() == "POST" and \
                                  "Content-Type" not in self.headers:
            self.headers["Content-Type"] = \
                        ["application/x-www-form-urlencoded"]

        self.response = None
        if self.body:
            self.body_producer = StringProducer(self.body)
        else:
            self.body_producer = None

    @defer.inlineCallbacks
    def fetch(self):
        request_headers = Headers(self.headers)
        response = yield agent.request(
            self.method,
            self.url,
            request_headers,
            self.body_producer)

        mr = self.maxRedirects
        while mr >= 1:
            if response.code in (301, 302, 303) and self.followRedirect:
                mr -= 1
                headers = dict(response.headers.getAllRawHeaders())
                location = headers.get("Location")
                if location:
                    if isinstance(location, types.ListType):
                        location = location[0]

                    #print("redirecting to:", location)
                    response = yield agent.request(
                        "GET",  # self.method,
                        location,
                        request_headers,
                        self.body_producer)
                else:
                    break
            else:
                break

        response.error = None
        response.headers = dict(response.headers.getAllRawHeaders())
        # HTTP 204 and 304 responses have no body
        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
        if response.code in (204, 304):
            response.body = ''
        else:
            d = defer.Deferred()
            response.deliverBody(Receiver(d))
            response.body = yield d
        response.request = self
        defer.returnValue(response)


def fetch(url, *args, **kwargs):
    """A non-blocking HTTP client.

    Example::

        d = httpclient.fetch("http://google.com")
        d.addCallback(on_response)

    By default the client does not follow redirects on HTTP 301, 302, 303
    or 307.

    Parameters:

    followRedirect: Boolean, to tell the client whether to follow redirects
                    or not. [default: False]

    maxRedirects: Maximum number of redirects to follow. This is to avoid
                  infinite loops cause by misconfigured servers.

    postdata: Data that accompanies the request. If a request ``method`` is not
              set but ``postdata`` is, then it is automatically turned into
              a ``POST`` and the ``Content-Type`` is set to
              ``application/x-www-form-urlencoded``.

    headers: A python dictionary containing HTTP headers for this request.
             Note that all values must be lists::

                 headers={"Content-Type": ["application/json"]}

    The response is an object with the following attributes:

    code: HTTP server response code.

    phrase: Text that describe the response code. e.g.: 302 ``See Other``

    headers: Response headers

    length: Content length

    body: The data, untouched
    """
    return HTTPClient(escape.utf8(url), *args, **kwargs).fetch()


class JsonRPC:
    """JSON-RPC client.

    Once instantiated, may be used to make multiple calls to the server.

    Example::

        cli = httpclient.JsonRPC("http://localhost:8888/jsonrpc")
        response1 = yield cli.echo("foobar")
        response2 = yield cli.sort(["foo", "bar"])

    Note that in the example above, ``echo`` and ``sort`` are remote methods
    provided by the server.
    """
    def __init__(self, url):
        self.__rpcId = 0
        self.__rpcUrl = url

    def __getattr__(self, attr):
        return functools.partial(self.__rpcRequest, attr)

    def __rpcRequest(self, method, *args):
        q = escape.json_encode({"method": method, "params": args,
                                "id": self.__rpcId})
        self.__rpcId += 1
        r = defer.Deferred()
        d = fetch(self.__rpcUrl, method="POST", postdata=q)

        def _success(response, deferred):
            if response.code == 200:
                data = escape.json_decode(response.body)
                error = data.get("error")
                if error:
                    deferred.errback(Exception(error))
                else:
                    deferred.callback(data.get("result"))
            else:
                deferred.errback(HTTPError(response.code, response.phrase))

        def _failure(failure, deferred):
            deferred.errback(failure)

        d.addCallback(_success, r)
        d.addErrback(_failure, r)
        return r
