import subprocess

from click import ClickException


def _run(*args, **options):
    kwargs = dict(
        check=True,
        # capture_output=True
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        # text=True
        universal_newlines=True,
    )
    kwargs.update(options)
    return subprocess.run(args, **kwargs)


def git(*args, **options):
    return _run("git", *args, **options)


def git_config(config):
    return git("config", "--get", config).stdout.rstrip()


def remote_url(remote="origin"):
    # remote = git_config(f"branch.master.remote")
    try:
        proc = git("config", "--get-all", f"remote.{remote}.url")
    except subprocess.CalledProcessError:
        raise ClickException(
            "Not in a Git repository or remote {} is not configured.".format(remote)
        )

    for url in proc.stdout.splitlines():
        if "github.com" in url:
            return url

    raise ClickException("Remote {} is not GitHub".format(remote))


def slug_from_url(url):
    _, slug = url.split("github.com", 1)
    slug = slug.lstrip(":/").rstrip("/")
    if slug.endswith(".git"):
        slug = slug[:-4]
    return slug


def guess_repository():
    return slug_from_url(remote_url())


def git_revision(rev: str):
    try:
        proc = git("rev-parse", "--verify", rev)
    except subprocess.CalledProcessError as err:
        raise ClickException(
            "Cannot interpret {!r} as a Git revision.\n[git] {}".format(
                rev, err.stderr.strip()
            )
        )

    return proc.stdout.strip()
