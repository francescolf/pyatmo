"""Define tests for the Legrand gateway home: NLG, NLY, NSD and NCO."""

import json
from unittest.mock import AsyncMock, patch

import pytest

import pyatmo
from pyatmo import DeviceType
from pyatmo.modules.device_types import DeviceCategory
from tests.common import MockResponse, load_fixture


@pytest.fixture
async def async_home_legrand(async_auth):
    """Home fixture built from the anonymised Legrand capture."""
    homesdata = json.loads(load_fixture("homesdata_legrand.json"))
    homestatus = json.loads(load_fixture("homestatus_legrand_home_id.json"))

    account = pyatmo.AsyncAccount(async_auth)

    with patch(
        "pyatmo.auth.AbstractAsyncAuth.async_post_api_request",
        AsyncMock(
            side_effect=[
                MockResponse(homesdata, 200),
                MockResponse(homestatus, 200),
            ],
        ),
    ):
        await account.async_update_topology()
        await account.async_update_status("legrand_home_id")

    return account.homes["legrand_home_id"]


async def test_legrand_home_shape(async_home_legrand):
    """Pin the fixture topology so a regenerated fixture fails loudly."""
    assert async_home_legrand.name == "Legrand Test Home"
    assert len(async_home_legrand.modules) == 11
    assert len(async_home_legrand.rooms) == 2

    gateway = async_home_legrand.modules["12:34:56:aa:00:01"]
    assert gateway.device_type == DeviceType.NLG
    assert gateway.modules == [
        "12:34:56:aa:00:02",
        "12:34:56:aa:00:02#1",
        "12:34:56:aa:00:02#2",
        "12:34:56:aa:00:02#3",
    ]

    meter = async_home_legrand.modules["12:34:56:aa:00:02"]
    assert meter.device_type == DeviceType.NLY
    assert meter.bridge == "12:34:56:aa:00:01"

    assert async_home_legrand.modules["12:34:56:aa:00:03"].device_type == DeviceType.NSD
    assert async_home_legrand.modules["12:34:56:aa:00:04"].device_type == DeviceType.NCO


async def test_nlevse_payload_parsing(async_auth):
    """Test Legrand electric vehicle charging station module parsing."""
    home = pyatmo.Home(
        async_auth,
        {
            "id": "home_evse",
            "modules": [{"id": "XXX", "type": "NLEVSE"}],
        },
    )

    module = home.modules["XXX"]
    assert module.device_type == DeviceType.NLEVSE
    assert module.device_category == DeviceCategory.meter

    await module.update(
        {
            "id": "XXX",
            "type": "NLEVSE",
            "firmware_revision": 94,
            "wifi_strength": 71,
            "charging_station_status": 0,
            "charging_station_error": 0,
            "current_charge_duration": 0,
            "current_charge_instant_consumption": 0,
            "current_total_charge_consumption": 0,
        },
    )

    assert module.firmware_revision == 94
    assert module.wifi_strength == 71
    assert module.charging_station_status == 0
    assert module.charging_station_error == 0
    assert module.current_charge_duration == 0
    assert module.current_charge_instant_consumption == 0
    assert module.current_total_charge_consumption == 0
    assert module.reachable is True
