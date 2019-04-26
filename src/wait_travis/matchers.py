from logging import getLogger

from .githubutils import git_revision

logger = getLogger(__name__)


class BasePrefixedNumberMatcher:
    @classmethod
    def parse(cls, url):
        if url.startswith(cls.prefix):
            number = url[len(cls.prefix) :]
            if number.isnumeric():
                return int(number)
        return None

    @classmethod
    def make_matcher(cls, url):
        num = cls.parse(url)
        assert num is not None
        logger.info(cls.message_format, num)
        return lambda build: bool(build.get(cls.key)) and int(build[cls.key]) == num
        # `int` for `build["number"]`


class PRMatcher(BasePrefixedNumberMatcher):
    prefix = "pr:"
    key = "pull_request_number"
    message_format = "Matching with PR: %s"


class BuildNumMatcher(BasePrefixedNumberMatcher):
    prefix = "num:"
    key = "number"
    message_format = "Matching with build number: #%s"


class BuildIDMatcher(BasePrefixedNumberMatcher):
    prefix = "id:"
    key = "id"
    message_format = "Matching with build ID: %s"


def make_sha_matcher(sha):
    logger.info("Matching with commit: %s", sha)
    return lambda build: build["commit"]["sha"] == sha


def make_matcher(url):
    """
    Create a predicate function from `url`.

    >>> f = make_matcher("pr:123")
    >>> f({"pull_request_number": 123})
    True
    >>> f({"pull_request_number": 456})
    False
    >>> f({"pull_request_number": None})
    False

    >>> f = make_matcher("num:123")
    >>> f({"number": "123"})
    True
    >>> f({"number": "456"})
    False

    """
    if not url:
        return lambda _: True

    for cls in [PRMatcher, BuildNumMatcher, BuildIDMatcher]:
        if cls.parse(url):
            return cls.make_matcher(url)

    if url.startswith("sha:"):
        url = url[len("sha:") :]
    return make_sha_matcher(git_revision(url))
