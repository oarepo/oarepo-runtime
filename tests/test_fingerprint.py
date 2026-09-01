# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

import hashlib
import json

import pytest
from packaging.version import Version

from oarepo_runtime import ext
from oarepo_runtime.cli import oarepo

LEVELS = ("major", "minor", "patch", "full")

# the algorithm is part of the fingerprint contract: changing it invalidates stored fingerprints
DIGEST = hashlib.sha512
EMPTY_DIGEST = DIGEST(b"").hexdigest()

CACHED_PROPERTIES = ("fingerprint", "_installed_packages")


def recompute_fingerprint(runtime) -> dict[str, str]:
    """Drop the cached fingerprint and read it again, as a level -> digest mapping."""
    runtime.__dict__.pop("fingerprint", None)
    return runtime.fingerprint


@pytest.fixture
def runtime(appctx):
    """Get the runtime extension with the cached fingerprint dropped around the test."""
    ext_ = appctx.extensions["oarepo-runtime"]
    for name in CACHED_PROPERTIES:
        ext_.__dict__.pop(name, None)
    yield ext_
    for name in CACHED_PROPERTIES:
        ext_.__dict__.pop(name, None)


@pytest.fixture
def installed_packages(runtime):
    """Replace the packages the fingerprint is computed from."""

    def _set(*specs: tuple[str, str]) -> None:
        # cached_property keeps its value in the instance __dict__
        runtime.__dict__["_installed_packages"] = [(name, Version(version)) for name, version in specs]

    return _set


@pytest.fixture
def fingerprint_config(appctx, monkeypatch):
    """Set the include/exclude regexes of the fingerprint."""

    def _set(included: list[str], excluded: list[str] | None = None) -> None:
        monkeypatch.setitem(appctx.config, "FINGERPRINT_PACKAGES", included)
        monkeypatch.setitem(appctx.config, "FINGERPRINT_EXCLUDED_PACKAGES", excluded or [])

    return _set


def test_fingerprint_returns_four_digests(runtime, installed_packages, fingerprint_config):
    installed_packages(("oarepo-runtime", "1.2.3"))
    fingerprint_config([r"oarepo-.*"])

    digests = recompute_fingerprint(runtime)

    assert set(digests) == set(LEVELS)
    for level, digest in digests.items():
        assert len(digest) == len(EMPTY_DIGEST), level
        assert digest != EMPTY_DIGEST, level


def test_fingerprint_of_real_environment(runtime, fingerprint_config):
    fingerprint_config([r"oarepo-.*", r"invenio-.*"])

    digests = recompute_fingerprint(runtime)

    assert digests["full"] != EMPTY_DIGEST
    assert recompute_fingerprint(runtime) == digests


def test_fingerprint_does_not_depend_on_package_order(runtime, installed_packages, fingerprint_config):
    fingerprint_config([r".*"])

    installed_packages(("aaa", "1.0.0"), ("bbb", "2.0.0"), ("ccc", "3.0.0"))
    ordered = recompute_fingerprint(runtime)

    installed_packages(("ccc", "3.0.0"), ("aaa", "1.0.0"), ("bbb", "2.0.0"))
    assert recompute_fingerprint(runtime) == ordered


def test_fingerprint_ignores_packages_not_matching_the_include_regexes(runtime, installed_packages, fingerprint_config):
    fingerprint_config([r"oarepo-.*"])

    installed_packages(("oarepo-runtime", "1.2.3"))
    expected = recompute_fingerprint(runtime)

    installed_packages(("oarepo-runtime", "1.2.3"), ("some-other-package", "9.9.9"))
    assert recompute_fingerprint(runtime) == expected


def test_fingerprint_ignores_excluded_packages(runtime, installed_packages, fingerprint_config):
    installed_packages(("invenio-records", "1.0.0"), ("invenio-records-resources", "2.0.0"))

    fingerprint_config([r"invenio-.*"], excluded=[r"invenio-records-resources"])
    without_excluded = recompute_fingerprint(runtime)

    fingerprint_config([r"invenio-.*"])
    assert recompute_fingerprint(runtime) != without_excluded


def test_fingerprint_is_empty_when_no_package_matches(runtime, installed_packages, fingerprint_config):
    installed_packages(("oarepo-runtime", "1.2.3"))
    fingerprint_config([r"nothing-matches-this"])

    assert recompute_fingerprint(runtime) == dict.fromkeys(LEVELS, EMPTY_DIGEST)


def test_fingerprint_is_none_on_missing_config(runtime, installed_packages, fingerprint_config):
    installed_packages(("oarepo-runtime", "1.2.3"))
    fingerprint_config([])

    assert recompute_fingerprint(runtime) is None


@pytest.mark.parametrize(
    ("bumped_version", "changed_levels"),
    [
        ("1.2.3", set()),
        ("1.2.4", {"patch", "full"}),
        ("1.3.0", {"minor", "patch", "full"}),
        ("2.0.0", {"major", "minor", "patch", "full"}),
        ("1.2.3+oarepoblabla", {"full"}),
        ("1.2.3.dev1", {"minor", "full"}),
        ("1.2.3.rc1", {"minor", "full"}),
    ],
)
def test_fingerprint_levels_react_to_the_bumped_version_part(
    runtime, installed_packages, fingerprint_config, bumped_version, changed_levels
):
    fingerprint_config([r"oarepo-.*"])

    installed_packages(("oarepo-runtime", "1.2.3"))
    before = recompute_fingerprint(runtime)

    installed_packages(("oarepo-runtime", bumped_version))
    after = recompute_fingerprint(runtime)

    assert {level for level in LEVELS if before[level] != after[level]} == changed_levels


class FakeDistribution:
    """Fake distribution object for testing."""

    def __init__(self, **metadata: dict):
        """Create a fake distribution object."""
        self.metadata = metadata


def test_installed_packages_skips_distributions_with_broken_metadata(runtime, monkeypatch):
    monkeypatch.setattr(
        ext,
        "distributions",
        lambda: [
            FakeDistribution(Name="good-package", Version="1.2.3"),
            FakeDistribution(Name="no-version"),
            FakeDistribution(Version="4.5.6"),
            FakeDistribution(Name="not-pep440", Version="this-is-not-a-version"),
        ],
    )

    assert runtime._installed_packages == [("good-package", Version("1.2.3"))]  # noqa: SLF001


def test_fingerprint_cli(appctx, runtime, fingerprint_config):
    fingerprint_config([r"oarepo-.*"])
    expected = recompute_fingerprint(runtime)

    result = appctx.test_cli_runner().invoke(oarepo, ["fingerprint"])

    assert result.exit_code == 0
    assert result.output == json.dumps(expected, indent=2) + "\n"


def test_fingerprint_cli_missing_config(appctx, runtime, fingerprint_config):
    fingerprint_config([r"oarepo-.*"])
    fingerprint_config([])

    result = appctx.test_cli_runner().invoke(oarepo, ["fingerprint"])

    assert result.exit_code == 1
    assert result.output == "Error: Packages fingerprinting is not configured.\n"


def test_fingerprint_in_repository_endpoint(client, runtime, fingerprint_config, info_blueprint):
    fingerprint_config([r"oarepo-.*"])
    expected = recompute_fingerprint(runtime)

    response = client.get("/.well-known/repository/")

    assert response.status_code == 200
    assert response.json["fingerprint"] == expected


def test_fingerprint_in_repository_endpoint_missing_config(client, runtime, fingerprint_config):
    fingerprint_config([r"oarepo-.*"])
    fingerprint_config([])

    response = client.get("/.well-known/repository/")

    assert response.status_code == 200
    assert "fingerprint" not in response.json
