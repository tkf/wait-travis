import itertools
import pprint
import time
import urllib.parse
from logging import DEBUG, getLogger

import click
import click_log
from click import ClickException

from . import __name__ as root_name
from .api import APIError, TravisAPI, build_duration, travis_build_id
from .githubutils import git_revision, guess_repository

root_logger = getLogger(root_name)
click_log.basic_config(root_logger)

logger = getLogger(__name__)


def msg(*args, **kwargs):
    click.secho(*args, err=True, **kwargs)


KNOWN_STATES = ("started", "passed", "failed", "canceled", "errored")


def is_finished(build):
    # Sanity check
    if build["state"] not in KNOWN_STATES:
        logger.warn("Unknown state: %s", build["state"])
    return build["state"] != "started"


def style_from_build(build):
    fg = {
        "started": "yellow",
        "passed": "green",
        "failed": "red",
        "canceled": "red",
        "errored": "red",
    }.get(build["state"])
    return dict(fg=fg)


def make_sleeper(interval: float):
    def sleep():
        time.sleep(interval)

    return sleep


def wait_build_impl(api, buildid, sleep, limit: int):
    if limit < 0:
        counter = itertools.count()
        den = ""
    else:
        counter = range(1, 1 + limit)
        den = "/{}".format(limit)

    for n in counter:
        click.echo(f"Polling {n}{den}... ", nl=False, err=True)
        build = api.get("build", buildid)
        click.echo(f"state: {build['state']}", err=True)
        if logger.isEnabledFor(DEBUG):
            logger.debug("%s", pprint.pformat(build))
        if is_finished(build):
            break
        sleep()
    return build


def wait_build(api, buildid, interval: float, limit: int):
    if limit > 0:
        logger.info(
            "Waiting up to %s minutes; polling every %s second(s)",
            interval * limit / 60,
            interval,
        )
    else:
        logger.info("Waiting indefinitely; polling every %s second(s)", interval)
    return wait_build_impl(api, buildid, make_sleeper(interval), limit)


def find_unfinished_builds(api, repository):
    slug = urllib.parse.quote(repository, safe="")
    result = api.get("repo", slug, "builds")
    return [build for build in result["builds"] if not is_finished(build)]


def show_build(build):
    msg(f"#{build['number']} ({build['id']}) ", nl=False)
    if build["state"] == "started":
        duration = build_duration(build).total_seconds() / 60
        msg(f"started {duration:.0f} min ago", **style_from_build(build), nl=False)
    else:
        msg(build["state"], **style_from_build(build), nl=False)
    if build.get("pull_request_title"):
        msg(": PR: ", nl=False)
        msg(build["pull_request_number"], fg="magenta", nl=False)
        msg(" ", nl=False)
        msg(build["pull_request_title"])
    else:
        branch = build["branch"]["name"]
        sha = build["commit"]["sha"][:7]
        title = build["commit"]["message"].split("\n", 1)[0].strip()
        msg(": ", nl=False)
        msg(f"{branch} ({sha})", fg="magenta", nl=False)
        msg(f" {title}")


def show_matched_builds(builds):
    if len(builds) == 1:
        msg("Found one matched build.", fg="green")
    else:
        msg(f"Found {len(builds)} matched builds.", fg="red")

    for build in builds:
        show_build(build)


def guess_unfinished_build(repository, matcher, api_candidates=None):
    if api_candidates is None:
        api_candidates = [TravisAPI.com(), TravisAPI.org()]

    for api in api_candidates:
        logger.info("Trying API at: %s", api.endpoint)

        try:
            builds = find_unfinished_builds(api, repository)
        except APIError:
            continue

        builds = list(filter(matcher, builds))
        show_matched_builds(builds)

        if len(builds) == 1:
            buildid = builds[0]["id"]
            assert isinstance(buildid, int)
            return api, str(buildid)
        elif len(builds) == 0:
            raise ClickException("No unfinished builds")
        else:
            raise ClickException("Multiple unfinished builds")


def parse_pr_number(url):
    if url.startswith("pr:"):
        number = url[len("pr:") :]
        if number.isnumeric():
            return int(number)
    return None


def make_pr_number_matcher(url):
    pr = parse_pr_number(url)
    assert pr is not None
    logger.info("Matching with PR: %s", pr)
    return lambda build: build.get("pull_request_number", None) == pr


def make_sha_matcher(sha):
    logger.info("Matching with commit: %s", sha)
    return lambda build: build["commit"]["sha"] == sha


def make_matcher(url):
    if not url:
        return lambda _: True
    elif parse_pr_number(url):
        return make_pr_number_matcher(url)
    else:
        return make_sha_matcher(git_revision(url))


@click.command()
@click_log.simple_verbosity_option(root_logger, "--log-level", "--verbosity")
@click.option("--interval", default=30.0)
@click.option("--limit", default=200)
@click.option("--browse/--no-browse")
@click.argument("url", required=False)
@click.pass_context
def main(ctx, url, browse, **kwargs):
    """
    Wait a success build running in Travis CI.
    """

    if url and url.startswith("https://travis-ci."):
        api = TravisAPI.from_url(url)
        buildid = travis_build_id(url)
    else:
        repository = guess_repository()
        logger.info("Repository found: %s", repository)
        api, buildid = guess_unfinished_build(repository, make_matcher(url))

        weburl = api.weburl_build(repository, buildid)
        click.echo(f"URL: {weburl}", err=True)
        if browse:
            click.launch(weburl)

    build = wait_build(api, buildid, **kwargs)

    state = build["state"]
    click.echo("Build result: ", nl=False, err=True)
    click.echo(click.style(state, fg="green" if state == "passed" else "red"), err=True)

    retcode = int(state != "passed")
    ctx.exit(retcode)


if __name__ == "__main__":
    main()
