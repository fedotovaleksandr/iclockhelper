import collections
import typing
from urllib.parse import ParseResult, parse_qs, urlparse
from urllib.request import Request

import dataclasses as da
import stringcase

from .models import AttendanceLog, AttendancePhotoLog, OperationLog, TableEnum


@da.dataclass(frozen=True)
class Info:
    fw_version: str = ''
    fp_count: int = 0
    transaction_count: str = ''
    user_count: int = 0
    main_time: str = ''
    max_finger_count: int = 0
    lock_fun_on: str = ''
    max_att_log_count: int = 0
    device_name: str = ''
    alg_ver: str = ''
    flash_size: str = ''
    free_flash_size: str = ''
    language: str = ''
    volume: str = ''
    dt_fmt: str = ''
    ip_address: str = ''
    is_tft: bool = False
    platform: str = ''
    brightness: str = ''
    backup_dev: str = ''
    oem_vendor: str = ''
    fp_version: str = ''


@da.dataclass(frozen=True)
class ZKRequest:
    sn: str
    push_version: str


@da.dataclass(frozen=True)
class GetRequest(ZKRequest):
    info: Info

    @staticmethod
    def from_req(req: Request):
        parsed_req = _ParsedRequest.from_req(req)
        (sn, pushver) = _extract_sn_version(parsed_req)
        return GetRequest(
            sn=sn,
            push_version=pushver,
            info=_fill_plain_info(parsed_req.params.get('INFO', '')),
        )


@da.dataclass(frozen=True)
class _ParsedRequest:
    req: Request
    method: str
    parseresult: ParseResult
    params: typing.Dict[str, typing.Any]
    body: bytes
    headers: typing.Dict[str, str]

    @classmethod
    def from_req(cls, req: Request) -> '_ParsedRequest':
        parseresult = urlparse(req.get_full_url())
        return cls(
            req=req,
            method=req.get_method(),
            headers=req.headers,
            body=req.data or b'',
            parseresult=parseresult,
            params={k: v if len(v) > 1 else v[0] for k, v in
                    parse_qs(parseresult.query).items()},
        )


@da.dataclass(frozen=True)
class CdataRequest(ZKRequest):
    method: str
    pin: str = ''
    save: bool = False
    body: str = ''
    stamp: str = ''
    operation_stamp: str = ''
    table: TableEnum = TableEnum.unknown
    attendance_log: typing.Optional[AttendanceLog] = None
    operation_log: typing.Optional[OperationLog] = None
    attendance_photo_log: typing.Optional[AttendancePhotoLog] = None

    @staticmethod
    def from_req(req: Request) -> 'CdataRequest':
        parsed_req = _ParsedRequest.from_req(req)

        (sn, pushver) = _extract_sn_version(parsed_req)
        method = parsed_req.method
        action = parsed_req.params.get('action', '')
        if action:
            return CdataRequest(
                sn=sn,
                push_version=pushver,
                method=method,
            )
        if method == 'GET':
            pin = _from_maps('PIN', 0, parsed_req.params)
            save = _from_maps('save', '', parsed_req.params) in ['1', 'Y', 'y', 'yes',
                                                                 'YES']
            return CdataRequest(
                sn=sn,
                push_version=pushver,
                method=method,
                pin=pin,
                save=save,
            )
        if method == 'POST':
            stamp = _from_maps('Stamp', '', parsed_req.params)
            operation_stamp = _from_maps('OpStamp', '', parsed_req.params)
            table = TableEnum(_from_maps('table', None, parsed_req.params))
            body = ''
            try:
                body = parsed_req.body.decode('ascii')
            except UnicodeDecodeError:
                try:
                    body = parsed_req.body.decode('gb18030')
                except UnicodeDecodeError:
                    pass

            operlog = att_log = att_photo = None
            if table == TableEnum.operlog:
                operlog = OperationLog.from_str(body)

            if table == TableEnum.attlog:
                att_log = AttendanceLog.from_str(body)

            if table == TableEnum.attphoto:
                att_photo = AttendancePhotoLog.from_request_pin(
                    _from_maps('PIN', '', parsed_req.params),
                    body,
                )

            return CdataRequest(
                sn=sn,
                push_version=pushver,
                method=method,
                table=table,
                stamp=stamp,
                operation_stamp=operation_stamp,
                body=body,
                attendance_log=att_log,
                attendance_photo_log=att_photo,
                operation_log=operlog
            )

        return CdataRequest(
            sn=sn,
            push_version=pushver,
            method=method,
        )


def _from_maps(key: str, defaut: typing.Any,
               *args: typing.Mapping[str, typing.Any]) -> typing.Any:
    for d in args:
        if key in d:
            return d[key]
    return defaut


def _extract_sn_version(req: _ParsedRequest) -> typing.Tuple[str, str]:
    pushver = req.params.get('pushver', 0.0)
    sn = _from_maps('SN', '', req.params)

    if not sn:
        sn = req.req.get_full_url()
        sn = (sn + 'SN=').split('SN=')[1].split('&')[0]
        if sn == '':
            sn = 'UNKNOWN'
    return sn, pushver


_info_map = collections.OrderedDict({
    'FWVersion': 'fw_version',
    'FPCount': 'fp_count',
    'VOLUME': 'volume',
    'IPAddress': 'ip_address',
    'IsTFT': 'is_tft',
    'OEMVendor': 'oem_vendor',
    'FPVersion': ''
}
)

_info_int_fields = frozenset(
    ['fp_count', 'transaction_count', 'user_count', 'max_finger_count',
     'max_att_log_count', ])


def _fill_plain_info(info: str) -> Info:
    if info:
        splitted_info = info.split(',')

        if len(splitted_info) >= 6:
            info = 'FWVersion={}\tUserCount={}\tFPCount={}' \
                   '\tTransactionCount={}\tIPAddress={}\tFPVersion={}\t' \
                .format(*splitted_info[:6])
        elif len(splitted_info) == 5:
            info = 'FWVersion={}\tUserCount={}\tFPCount={}' \
                   '\tTransactionCount={}\tIPAddress={}\t' \
                .format(*splitted_info)
        elif len(splitted_info) == 4:
            info = 'FWVersion={}\tUserCount={}\tFPCount={}' \
                   '\tTransactionCount={}\t' \
                .format(*splitted_info)

    return _fill_info(info)


def _fill_info(info: str) -> Info:
    pd = _set_value_dict(info)
    info_fileds = frozenset([f.name for f in da.fields(Info)])
    info_data = {}
    for key in pd.keys():
        normal_key = key
        if key[0] == '~':
            normal_key = key[1:]

        if normal_key in _info_map:
            normal_key = _info_map[normal_key]
        else:
            normal_key = stringcase.snakecase(normal_key)

        if normal_key in info_fileds:
            if normal_key == 'platform' and '_TFT' in pd[key]:
                info_data['is_tft'] = True
            value = pd[key]
            # ints
            if normal_key in _info_int_fields:
                value = 0
                try:
                    value = int(pd[key])
                except ValueError:
                    pass

            if normal_key == 'max_att_log_count':
                value *= 10000
            if normal_key == 'max_finger_count':
                value *= 100
            info_data[normal_key] = value

    return Info(
        **info_data  # type: ignore
    )


def _set_value_dict(data: str) -> typing.Mapping[str, typing.Any]:
    d = {}
    for line in data.split('\t'):
        if line:
            v = line.split('\r')[0]
        else:
            v = line
        nv = v.split('=', 1)
        if len(nv) > 1:
            try:
                v = str(nv[1])
                d[nv[0]] = v
            except ValueError:
                pass
    return d
