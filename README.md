
### iclockhelper

[![Build Status](https://travis-ci.org/fedotovaleksandr/iclockhelper.svg?branch=master)](https://travis-ci.org/fedotovaleksandr/iclockhelper)

Helper library to parse income request from IClock ADMS(like ZKTeco)


### Install
```
pip install iclockhelper
```


### Usage
```
    from urllib.request import Request
    from django.core.handlers.wsgi import WSGIRequest
    from django.http import HttpResponse
    import iclockhelper

    # /iclock/cdata
    def cdataView(request: WSGIRequest):
        #get data from device
        zk_request = create_request(request)
        cdata_req = iclockhelper.CdataRequest.from_req(zk_request)
        print(cdata_req)
        return HttpResponse('OK')

    # /iclock/fdata
    def fdataView(request: WSGIRequest):
        # not implemented
        return HttpResponse('OK')

    # /iclock/getreq
    def getreqView(request: WSGIRequest):
        zk_request = create_request(request)
        get_req = iclockhelper.GetRequest.from_req(zk_request)
        print(get_req)
        return HttpResponse('OK')

    # /iclock/devicecmd
    def devpostView(request: WSGIRequest):
        # not implemented
        return HttpResponse('OK')


    def create_request(req: WSGIRequest)->iclockhelper.Request:
        return  Request(
            headers=req.headers,
            method=req.method,
            url=req.get_raw_uri(),
            data=req.body,
        )
```


### Note

This project has been set up using PyScaffold 3.2.3. For details and usage
information on PyScaffold see https://pyscaffold.org/.
