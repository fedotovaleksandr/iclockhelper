import typing
from urllib.parse import urlencode
from urllib.request import Request

import dataclasses as da


@da.dataclass()
class DeviceRequestBuilder:
    sn: str
    iclock_host: str
    fw_version: str

    def request(
            self,
            path: str,
            query: typing.Dict[str, typing.Any] = None,
            body: bytes = b'',
    ) -> Request:
        query = {} if query is None else query
        query['SN'] = self.sn
        str_query = ''
        if query:
            str_query = urlencode(query)

        url = "{:s}{:s}?{:s}".format(self.iclock_host, path, str_query)

        if body:
            req = Request(url, body)
        else:
            req = Request(url)
        req.headers["Content-type"] = "text/plain"

        return req

    def getrequest(self, query: typing.Dict[str, typing.Any]) -> Request:
        return self.request(
            "/iclock/getrequest",
            query=query
        )

    def postcmdrequest(self, id, cmd, ret) -> Request:
        return self.request(
            "/iclock/devicecmd",
            body="ID={:s}&Return={:s}&CMD={:s}".format(id, ret, cmd).encode('ascii')
        )

    def cdatarequest(
            self,
            query: typing.Dict[str, typing.Any] = None,
            body: bytes = b''
    ) -> Request:
        return self.request(
            '/iclock/cdata',
            query,
            body
        )
