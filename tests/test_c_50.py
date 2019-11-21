import datetime
import typing
import unittest

import dataclasses as da

from iclockhelper.models import (
    AlarmEnum,
    Fingerprint,
    Operation,
    OperationEnum,
    TableEnum,
    Transaction,
    User
)
from iclockhelper.requests import CdataRequest, GetRequest

from .common import DeviceRequestBuilder

_SN = 'SN_C_50'
_ICLOCK_HOST = 'http://localhost'
_FW_VERSION = '2.4.0'
_LANGUAGE = 69
_USER_COUNT = 3
_FP_COUNT = 2
_TRANS_COUNT = 10
_STAMP = '11122'
_OP_STAMP = '9999'


def _create_many_trans_body(transactions: typing.List[Transaction]) -> str:
    return "\n".join([
        "{:s}\t{:s}\t{:s}\t{:s}\t{:s}\t{:s}".format(
            trans.pin,
            trans.server_datetime.strftime('%Y-%m-%d %H:%M:%S')
            if trans.server_datetime else '',
            trans.check_type,
            trans.verify_code,
            trans.work_code,
            trans.reserved,
        ) for trans in
        transactions])


def _create_many_user_body(users: typing.List[User]) -> str:
    return "\n".join(
        [
            "USER PIN={:s}\tName={:s}\tPri={:s}\tPasswd={:s}"
            "\tCard={:s}\tGrp={:s}\tTZ={:s}\tVerify={:s}\tViceCard={:s}".format(
                u.pin,
                u.name,
                u.privileges,
                u.password,
                u.card,
                u.group,
                u.tz,
                u.verify,
                u.vice_card,
            ) for u in users])


def _create_many_fingerprint_body(fingerprints: typing.List[Fingerprint]) -> str:
    return "\n".join(
        ["FP PIN={:s}\tFID={:s}\tValid={:s}\tTMP={:s}".format(f.pin, f.fid, '1', f.tmp)
         for f in fingerprints])


def _create_many_operation_body(opers: typing.List[Operation]) -> str:
    return "\n".join(
        ["OPLOG {:s}\t{:s}\t{:s}\t{:s}\t{:s}\t{:s}\t{:s}".format(
            o.operation.value,
            o.admin,
            o.server_datetime.strftime('%Y-%m-%d %H:%M:%S')
            if o.server_datetime else '',
            o.object,
            o.param_1,
            o.param_2,
            o.param_3,
        ) for o in opers])


class ModelC50Test(unittest.TestCase):
    def setUp(self) -> None:
        self.req_builder = DeviceRequestBuilder(
            sn=_SN,
            iclock_host=_ICLOCK_HOST,
            fw_version=_FW_VERSION,
        )

    def test_cdata_all_options(self):
        base_datetime = datetime.datetime(
            year=2000,
            month=1,
            day=1,
            hour=1,
            minute=1,
            second=0)

        trans = [
            Transaction(
                pin='pin1',
                server_datetime=base_datetime + datetime.timedelta(seconds=5),
                raw=''
            ),
            Transaction(
                pin='pin1',
                server_datetime=base_datetime + datetime.timedelta(seconds=10),
                raw=''
            )
        ]
        body = _create_many_trans_body(trans)
        req = self.req_builder.cdatarequest(
            query={
                'options': 'all',
                'pushver': _FW_VERSION,
                'language': _LANGUAGE,
                'PushOptionsFlag': 1
            },
            body=body.encode('ascii')
        )
        cdata_req = CdataRequest.from_req(req)
        self.assertEqual(_SN, cdata_req.sn)
        self.assertTrue(_FW_VERSION, cdata_req.push_version)

    def test_cdata_operlog_oplog(self):
        base_datetime = datetime.datetime(year=2000, month=1, day=1, hour=1, minute=1,
                                          second=0)

        operations = [
            Operation(
                object='51',
                param_1='p11',
                param_2='p12',
                param_3='p13',
                raw='',
                admin='a1',
                operation=OperationEnum.alarm,
                alarm=AlarmEnum.door_open_detected,
                server_datetime=base_datetime + datetime.timedelta(seconds=5),
            ),
            Operation(
                object='o2',
                param_1='p21',
                param_2='p22',
                param_3='p23',
                raw='',
                admin='a1',
                operation=OperationEnum.enter_the_menu,
                server_datetime=base_datetime + datetime.timedelta(seconds=5),
            )
        ]
        body = _create_many_operation_body(operations)
        req = self.req_builder.cdatarequest(
            query={
                'table': TableEnum.operlog.value,
                'OpStamp': _OP_STAMP
            },
            body=body.encode('ascii'),
        )
        cdata_req = CdataRequest.from_req(req)
        self.assertEqual(_SN, cdata_req.sn)
        self.assertTrue(_OP_STAMP, cdata_req.operation_stamp)
        self.assertTrue(TableEnum.operlog, cdata_req.table)
        self.assertIsNotNone(cdata_req.operation_log)
        self.assertEqual(len(operations), len(cdata_req.operation_log.operations))
        for i in range(len(operations)):
            expected = da.asdict(operations[i])
            actual = da.asdict(cdata_req.operation_log.operations[i])
            del expected['raw']
            del actual['raw']
            self.assertEqual(
                expected,
                actual,
            )

    def test_cdata_operlog_user(self):
        operations = [
            User(
                pin='pin1',
                name='name1',
                password='pass1',
                card='card1',
                group='group1',
                tz='tz1',
                privileges='privileges1',
                verify='verify1',
                vice_card='vise_card1',
                raw=''
            ),
            User(
                pin='pin2',
                name='name2',
                password='pass2',
                card='card2',
                group='group2',
                tz='tz2',
                privileges='privileges2',
                verify='verify2',
                vice_card='vise_card2',
                raw=''
            )
        ]
        body = _create_many_user_body(operations)
        req = self.req_builder.cdatarequest(
            query={
                'table': TableEnum.operlog.value,
                'OpStamp': '9999'
            },
            body=body.encode('ascii'),
        )
        cdata_req = CdataRequest.from_req(req)
        self.assertEqual(_SN, cdata_req.sn)
        self.assertTrue(_OP_STAMP, cdata_req.operation_stamp)
        self.assertTrue(TableEnum.operlog, cdata_req.table)
        self.assertIsNotNone(cdata_req.operation_log)
        self.assertEqual(len(operations), len(cdata_req.operation_log.users))
        for i in range(len(operations)):
            expected = da.asdict(operations[i])
            actual = da.asdict(cdata_req.operation_log.users[i])
            del expected['raw']
            del actual['raw']
            self.assertEqual(
                expected,
                actual,
            )

    def test_cdata_operlog_fp(self):
        operations = [
            Fingerprint(
                pin='pin1',
                fid='fid1',
                tmp='tmp1',
                raw=''
            ),
            Fingerprint(
                pin='pin2',
                fid='fid2',
                tmp='tmp2',
                raw=''
            )
        ]
        body = _create_many_fingerprint_body(operations)
        req = self.req_builder.cdatarequest(
            query={
                'table': TableEnum.operlog.value,
                'OpStamp': '9999'
            },
            body=body.encode('ascii'),
        )
        cdata_req = CdataRequest.from_req(req)
        self.assertEqual(_SN, cdata_req.sn)
        self.assertTrue(_OP_STAMP, cdata_req.operation_stamp)
        self.assertTrue(TableEnum.operlog, cdata_req.table)
        self.assertIsNotNone(cdata_req.operation_log)
        self.assertEqual(len(operations), len(cdata_req.operation_log.fingerprints))
        for i in range(len(operations)):
            expected = da.asdict(operations[i])
            actual = da.asdict(cdata_req.operation_log.fingerprints[i])
            del expected['raw']
            del actual['raw']
            self.assertEqual(
                expected,
                actual,
            )

    def test_cdata_attlog(self):
        base_datetime = datetime.datetime(year=2000, month=1, day=1, hour=1, minute=1,
                                          second=0)

        operations = [
            Transaction(
                pin='pin1',
                server_datetime=base_datetime + datetime.timedelta(seconds=5),
                check_type='ct1',
                verify_code='vc1',
                work_code='wc1',
                reserved='re1',
                raw=''
            ),
            Transaction(
                pin='pin1',
                server_datetime=base_datetime + datetime.timedelta(seconds=10),
                check_type='ct2',
                verify_code='vc2',
                work_code='wc2',
                reserved='re2',
                raw=''
            )
        ]
        body = _create_many_trans_body(operations)
        req = self.req_builder.cdatarequest(
            query={'table': TableEnum.attlog.value, 'Stamp': '9999'},
            body=body.encode('ascii'),
        )
        cdata_req = CdataRequest.from_req(req)
        self.assertEqual(_SN, cdata_req.sn)
        self.assertTrue(_STAMP, cdata_req.stamp)
        self.assertTrue(TableEnum.attlog, cdata_req.table)
        self.assertIsNotNone(cdata_req.attendance_log)
        self.assertEqual(len(operations), len(cdata_req.attendance_log.transactions))
        for i in range(len(operations)):
            expected = da.asdict(operations[i])
            actual = da.asdict(cdata_req.attendance_log.transactions[i])
            del expected['raw']
            del actual['raw']
            self.assertEqual(
                expected,
                actual,
            )

    def test_getreq(self):
        req = self.req_builder.getrequest(
            query={
                "INFO": "{:s},{:d},{:d},{:d},{:s}".format(
                    _FW_VERSION,
                    _USER_COUNT,
                    _FP_COUNT,
                    _TRANS_COUNT,
                    _ICLOCK_HOST)
            }
        )
        get_req = GetRequest.from_req(req)

        self.assertEqual(_SN, get_req.sn)
        self.assertEqual(_FW_VERSION, get_req.info.fw_version)
        self.assertEqual(_USER_COUNT, get_req.info.user_count)
        self.assertEqual(_FP_COUNT, get_req.info.fp_count)
        self.assertEqual(_TRANS_COUNT, get_req.info.transaction_count)

    def test_devpostreq(self):
        self.assertTrue(True)

    def test_fdatareq(self):
        self.assertTrue(True)
