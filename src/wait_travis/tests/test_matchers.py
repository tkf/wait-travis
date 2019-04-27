from ..matchers import make_matcher


def test_branch_matcher():
    f = make_matcher("branch:dev")
    assert f({"branch": {"name": "dev"}})
    assert not f({"branch": {"name": "master"}})
