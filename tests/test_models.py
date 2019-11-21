import datetime

import pytz as pytz

from iclockhelper.models import ServerDatetimeMixin


def test_server_datetime_mixin():
    base_datetime = datetime.datetime(
        year=2000,
        month=1,
        day=1,
        hour=1,
        minute=1,
        second=0,
        tzinfo=pytz.timezone("UTC"),
    )
    gmt = pytz.timezone("GMT")
    actual_time = ServerDatetimeMixin(server_datetime=base_datetime).correct_datetime(
        gmt
    )
    for f in ['year', 'month', 'day', 'hour', 'minute', 'second']:
        assert getattr(base_datetime, f) == getattr(actual_time, f)

    assert actual_time.tzinfo == gmt
