from app.core.enums import ServiceStatus, RequestStatus


def test_service_status_constants():
    assert ServiceStatus.REQUEST == 'REQUEST'
    assert ServiceStatus.CONFIRMED == 'CONFIRMED'
    assert ServiceStatus.CANCELLED == 'CANCELLED'


def test_service_status_label():
    assert ServiceStatus.label('REQUEST') == 'Requested'
    assert ServiceStatus.label('CONFIRMED') == 'Confirmed'


def test_request_status_normalize_legacy():
    assert RequestStatus.normalize('BOOKED') == 'CONFIRMED'
    assert RequestStatus.normalize('COMPLETED') == 'INVOICED'
    assert RequestStatus.normalize('IN_PROGRESS') == 'CONFIRMED'
    assert RequestStatus.normalize('QUOTED') == 'CONFIRMED'


def test_request_status_label_legacy():
    assert RequestStatus.label('BOOKED') == 'Confirmed'
    assert RequestStatus.label('COMPLETED') == 'Invoiced'


def test_request_status_all_values():
    assert 'REQUEST' in RequestStatus.ALL
    assert 'CONFIRMED' in RequestStatus.ALL
    assert 'INVOICED' in RequestStatus.ALL
