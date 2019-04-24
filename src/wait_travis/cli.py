import itertools
import pprint
import time
from logging import DEBUG, getLogger

import click
import click_log

from . import __name__ as root_name
from .api import TravisAPI, travis_build_id

root_logger = getLogger(root_name)
click_log.basic_config(root_logger)

logger = getLogger(__name__)


def wait_build(api, buildid, interval: float, limit: int):
    if limit < 0:
        counter = itertools.count()
        den = ""
    else:
        counter = range(1, 1 + limit)
        den = "/{}".format(limit)

    for n in counter:
        logger.info("Polling %d%s...", n, den)
        build = api.get("build", buildid)
        logger.debug("Relived state = %r", build["state"])
        if logger.isEnabledFor(DEBUG):
            logger.debug("%s", pprint.pformat(build))
        if build["state"] in ("passed", "failed"):
            break
        time.sleep(interval)
    return build


@click.command()
@click_log.simple_verbosity_option(root_logger, "--log-level", "--verbosity")
@click.option("--interval", default=30.0)
@click.option("--limit", default=1000)
@click.argument("url")
@click.pass_context
def main(ctx, url, **kwargs):
    api = TravisAPI.from_url(url)
    buildid = travis_build_id(url)
    build = wait_build(api, buildid, **kwargs)

    state = build["state"]
    click.echo("Build result: ", nl=False, err=True)
    click.echo(click.style(state, fg="green" if state == "passed" else "red"), err=True)

    retcode = int(state != "passed")
    ctx.exit(retcode)


if __name__ == "__main__":
    main()
