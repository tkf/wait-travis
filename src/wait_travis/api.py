import subprocess
from urllib.parse import urlparse

import requests

TOKENS = {}


class APIError(ValueError):
    pass


def get_token(endpoint):
    try:
        return TOKENS[endpoint]
    except KeyError:
        pass

    if "//api.travis-ci.com" in endpoint:
        clioptions = ["--com"]
    elif "//api.travis-ci.org" in endpoint:
        clioptions = ["--org"]
    else:
        raise ValueError("Unknown URL: {}".format(endpoint))

    cmd = ["travis", "token"]
    cmd.extend(clioptions)
    token = subprocess.check_output(cmd, universal_newlines=True).strip()

    TOKENS[endpoint] = token
    return token


class TravisAPI:
    @classmethod
    def com(cls):
        return cls("https://api.travis-ci.com")

    @classmethod
    def org(cls):
        return cls("https://api.travis-ci.org")

    @classmethod
    def from_url(cls, url):
        if "//travis-ci.com" in url:
            return cls.com()
        elif "//travis-ci.org" in url:
            return cls.org()
        raise ValueError("Unknown URL: {}".format(url))

    def __init__(self, endpoint):
        self.endpoint = endpoint

    def get_token(self):
        return get_token(self.endpoint)

    def get_response(self, *path):
        token = self.get_token()
        headers = {"Authorization": "token {}".format(token), "Travis-API-Version": "3"}
        url = "/".join((self.endpoint, *path))
        return requests.get(url, headers=headers)

    def get(self, *path, **kwargs):
        result = self.get_response(*path, **kwargs).json()
        if result.get("@type", "error") == "error":
            raise APIError(result)
        return result

    def weburl(self):
        return "https://" + self.endpoint[len("https://api.") :]

    def weburl_build(self, repository, buildid):
        return "/".join([self.weburl(), repository, "builds", buildid])


def travis_build_id(url):
    result = urlparse(url)
    p0, _user, _repo, builds, buildid = result.path.split("/", 4)
    assert p0 == ""
    assert builds == "builds"
    return buildid
