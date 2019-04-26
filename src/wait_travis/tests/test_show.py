from datetime import datetime, timedelta

import pytest

from ..cli import show_matched_builds

pasttime = datetime.utcnow() - timedelta(minutes=10)

builds_examples = [
    [
        {
            "id": 109539786,
            "number": "83",
            "state": "created",
            "duration": None,
            "pull_request_title": None,
            "pull_request_number": None,
            "started_at": None,
            "finished_at": None,
            "branch": {"name": "master"},
            "commit": {
                "sha": "d03754022785584c0bd211b8fd559e2779527ba5",
                "message": "Commit message title",
            },
            "updated_at": "2019-04-25T03:04:47.914Z",
        },
        {
            "id": 109539444,
            "number": "82",
            "state": "started",
            "duration": None,
            "pull_request_title": None,
            "pull_request_number": None,
            "started_at": pasttime.isoformat() + "Z",
            "finished_at": None,
            "branch": {"name": "master"},
            "commit": {
                "sha": "283e62683ea8f9428f4bf6e2f45ae9f46853ddf2",
                "message": "Commit message title",
            },
            "updated_at": "2019-04-25T02:59:17.313Z",
        },
        {
            "id": 109539437,
            "number": "81",
            "state": "started",
            "duration": None,
            "pull_request_title": "Pull request title",
            "pull_request_number": 192,
            "started_at": pasttime.isoformat() + "Z",
            "finished_at": None,
            "branch": {"name": "master"},
            "commit": {
                "sha": "283e62683ea8f9428f4bf6e2f45ae9f46853ddf2",
                "message": "Commit message title",
            },
            "updated_at": "2019-04-25T02:59:17.313Z",
        },
        {
            "id": 109384865,
            "number": "80",
            "state": "passed",
            "duration": 526,
            "pull_request_title": None,
            "pull_request_number": None,
            "started_at": "2019-04-24T05:36:51Z",
            "finished_at": "2019-04-24T05:45:37Z",
            "branch": {"name": "dev"},
            "commit": {
                "sha": "e33b494993f2d32bed98df244ebfcb00d9adc436",
                "message": "Commit message title",
            },
            "updated_at": "2019-04-24T05:45:37.579Z",
        },
        {
            "id": 109380829,
            "number": "79",
            "state": "failed",
            "duration": 623,
            "pull_request_title": None,
            "pull_request_number": None,
            "started_at": "2019-04-24T04:19:46Z",
            "finished_at": "2019-04-24T04:30:09Z",
            "branch": {"name": "dev"},
            "commit": {
                "id": 193015983,
                "sha": "1f026c805dec91c0bdeba356f424a510b354c584",
                "message": (
                    # For testing that message body is ignored:
                    "Commit message title\n"
                    "\n"
                    "Commit message body"
                ),
            },
            "updated_at": "2019-04-24T04:30:09.294Z",
        },
    ]
]
builds_examples.append(
    [next(build for build in builds_examples[0] if build["state"] == "started")]
)
builds_examples.append(
    [next(build for build in builds_examples[0] if build["state"] == "created")]
)
builds_examples.append(
    [next(build for build in builds_examples[0] if build["state"] == "passed")]
)


@pytest.mark.parametrize("builds", builds_examples)
def test_show_matched_builds(builds):
    show_matched_builds(builds)
