from unittest.mock import Mock

import pytest

from ..cli import wait_build_impl


@pytest.mark.parametrize("state", ["passed", "failed"])
def test_immediately_terminate(state):
    def sleep():
        raise AssertionError("must not be called")

    api = Mock()
    api.get.return_value = {"state": state}
    wait_build_impl(api, None, sleep, limit=-1)


@pytest.mark.parametrize("state", ["passed", "failed"])
def test_three_times(state):
    builds = [
        # dicts to be returned from `api.get`:
        {"state": "started"},
        {"state": "started"},
        {"state": state},
    ]

    def get(*_):
        return builds.pop(0)

    api = Mock()
    api.get.side_effect = get
    sleep = Mock()
    wait_build_impl(api, None, sleep, limit=-1)
    assert sleep.call_count == 2
