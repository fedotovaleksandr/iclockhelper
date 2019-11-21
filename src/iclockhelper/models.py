import datetime
import enum
import typing

import dataclasses as da
import stringcase

UNKNOWN = 'UNKNOWN'


class UnknowableEnum(enum.Enum):
    @classmethod
    def _missing_(cls, value):
        return cls.unknown


class TableEnum(UnknowableEnum):
    unknown = UNKNOWN
    operlog = 'OPERLOG'
    attlog = 'ATTLOG'
    attphoto = 'ATTPHOTO'


class AlarmEnum(UnknowableEnum):
    unknown = UNKNOWN
    door_close_detected = '50'
    door_open_detected = '51'
    machine_been_broken = '55'
    out_door_button = '53'
    door_broken_accidentally = '54'
    try_invalid_verification = '58'
    alarm_cancelled = '65535'


class OperationEnum(UnknowableEnum):
    unknown = UNKNOWN
    start_up = '0'
    shutdown = '1'
    validation_failure = '2'
    alarm = '3'
    enter_the_menu = '4'
    change_settings = '5'
    registration_fingerprint = '6'
    registration_password = '7'
    card_registration = '8'
    delete_user = '9'
    delete_fingerprints = '10'
    delete_the_password = '11'
    delete_rf_card = '12'
    remove_data = '13'
    mf_create_cards = '14'
    mf_registration_cards = '15'
    mf_registration_cards_2 = '16'
    mf_registration_card_deleted = '17'
    mf_clearance_card_content = '18'
    moved_to_the_registration_card_data = '19'
    the_data_in_the_card_copied_to_the_machine = '20'
    set_time = '21'
    restore_factory_settings = '22'
    delete_records_access = '23'
    remove_administrator_rights = '24'
    group_set_up_to_amend_access = '25'
    modify_user_access_control_settings = '26'
    access_time_to_amend_paragraph = '27'
    amend_unlock_portfolio = '28'
    unlock = '29'
    registration_of_new_users = '30'
    fingerprint_attribute_changes = '31'
    stress_alarm = '32'


@da.dataclass(frozen=True)
class ServerDatetimeMixin:
    server_datetime: typing.Optional[datetime.datetime]

    def correct_datetime(
            self, tz: datetime.timezone
    ) -> typing.Optional[datetime.datetime]:
        if not self.server_datetime:
            return None
        return datetime.datetime(
            year=self.server_datetime.year,
            month=self.server_datetime.month,
            day=self.server_datetime.day,
            hour=self.server_datetime.hour,
            minute=self.server_datetime.minute,
            second=self.server_datetime.second,
            tzinfo=tz,
        )


@da.dataclass(frozen=True)
class Transaction(ServerDatetimeMixin):
    pin: str
    raw: str
    check_type: str = ''
    verify_code: str = ''
    work_code: str = ''
    reserved: str = ''

    @classmethod
    def from_str(cls, line: str) -> 'Transaction':
        flds = line.split('\t') + ['', '', '', '', '', '']
        pin = flds[0]
        server_datetime = None
        try:
            server_datetime = datetime.datetime.strptime(flds[1], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
        checktype = flds[2]
        verifycode = flds[3]
        work_code = flds[4]
        reserved = flds[5]

        return cls(
            pin=pin,
            server_datetime=server_datetime,
            check_type=checktype,
            verify_code=verifycode,
            work_code=work_code,
            reserved=reserved,
            raw=line,
        )


_user_fieds_map = {
    'PIN': 'pin',
    'Passwd': 'password',
    'Card': 'card',
    'Grp': 'group',
    'TZ': 'tz',
    'Pri': 'privileges',
    'Verify': 'verify',
    'ViceCard': 'vice_card',
}


@da.dataclass(frozen=True)
class User:
    pin: str
    name: str
    password: str
    card: str
    group: str
    tz: str
    privileges: str
    raw: str
    verify: str = ''
    vice_card: str = ''

    @classmethod
    def from_str(cls, line: str) -> 'User':
        flds = _build_operlog_fields(line)
        return _fill_da_from_mapping(
            cls,
            _user_fieds_map,
            **{
                'raw': line,
                **flds
            }
        )


_DA = typing.TypeVar('_DA', covariant=True)


def _fill_da_from_mapping(
        model_type: typing.Type[_DA],
        mapping: typing.Mapping[str, str],
        **kwargs: typing.Any,
) -> _DA:
    model_data = {}
    fields_names = [f.name for f in da.fields(model_type)]
    for key, val in kwargs.items():
        normal_key = stringcase.snakecase(key)
        if key in mapping:
            normal_key = mapping[key]
        if normal_key in fields_names:
            model_data[normal_key] = val
    return model_type(**model_data)  # type: ignore


_fingerprint_fields_map = {
    'PIN': 'pin',
    'FID': 'fid',
    'TMP': 'tmp',
}


@da.dataclass(frozen=True)
class Fingerprint:
    pin: str
    fid: str
    tmp: str
    raw: str

    @classmethod
    def from_str(cls, line: str) -> 'Fingerprint':
        flds = _build_operlog_fields(line)
        return _fill_da_from_mapping(
            cls,
            _fingerprint_fields_map,
            **{
                'raw': line,
                **flds
            }
        )


@da.dataclass(frozen=True)
class Operation(ServerDatetimeMixin):
    object: str
    param_1: str
    param_2: str
    param_3: str
    raw: str
    operation: OperationEnum
    admin: str
    alarm: AlarmEnum = AlarmEnum.unknown

    @classmethod
    def from_str(cls, line: str) -> 'Operation':
        flds = line.split('\t')
        logtime = None
        try:
            logtime = datetime.datetime.strptime(flds[2], '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass
        object = flds[3]
        operation = OperationEnum(flds[0])
        return Operation(
            admin=flds[1],
            operation=operation,
            server_datetime=logtime,
            object=object,
            param_1=flds[4],
            param_2=flds[5],
            param_3=flds[6],
            raw=line,
            alarm=AlarmEnum(
                object) if operation == OperationEnum.alarm else AlarmEnum.unknown
        )


@da.dataclass(frozen=True)
class OperationLog:
    raw: str
    users: typing.List[User] = da.field(default_factory=list)
    fingerprints: typing.List[Fingerprint] = da.field(default_factory=list)
    operations: typing.List[Operation] = da.field(default_factory=list)

    @classmethod
    def from_str(cls, data: str) -> 'OperationLog':
        users = []
        fingerprints = []
        operations = []
        for line in data.split('\n'):
            ops = line.split(' ', 1)

            if ops[0] == 'OPLOG':
                operations.append(Operation.from_str(ops[1]))
            if ops[0] == 'USER':
                users.append(User.from_str(ops[1]))
            elif ops[0] == 'FP':
                fingerprints.append(Fingerprint.from_str(ops[1]))
        return cls(
            users=users,
            operations=operations,
            fingerprints=fingerprints,
            raw=data
        )


@da.dataclass(frozen=True)
class AttendanceLog:
    raw: str
    transactions: typing.List[Transaction] = da.field(default_factory=list)

    @classmethod
    def from_str(cls, data: str) -> 'AttendanceLog':
        transactions = []
        for line in data.split('\n'):
            transactions.append(Transaction.from_str(line))
        return cls(
            transactions=transactions,
            raw=data,
        )


@da.dataclass(frozen=True)
class AttendancePhotoLog(ServerDatetimeMixin):
    raw: str
    pin: str = ''
    is_uploadphoto: bool = False
    is_realupload: bool = False
    data: str = ''

    @classmethod
    def from_request_pin(cls, req_pin: str, body: str) -> 'AttendancePhotoLog':
        pin_split = req_pin.split('.')[0].split('-')  # type: typing.List[str]
        dt = pin_split[0]
        pin = ''
        if len(pin_split) == 2:  # Success Picture
            pin = pin_split[1]
        server_datetime = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
        image_data = ''
        is_uploadphoto = False
        is_realupload = False

        if 'CMD=uploadphoto' in body:
            image_data = body.split('CMD=uploadphoto')[1][1:]
            is_uploadphoto = True
        if 'CMD=realupload' in body:
            image_data = body.split('CMD=realupload')[1][1:]
            is_realupload = True

        return cls(
            pin=pin,
            server_datetime=server_datetime,
            is_uploadphoto=is_uploadphoto,
            is_realupload=is_realupload,
            data=image_data,
            raw=req_pin + body,
        )


def _build_operlog_fields(ops_1: str) -> typing.Dict[str, typing.Any]:
    flds = {}
    for item in ops_1.split('\t'):
        index = item.find('=')
        if index > 0:
            flds[item[:index]] = item[index + 1:]

    return flds
