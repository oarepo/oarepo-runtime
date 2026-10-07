# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Pluggable fixtures for ``invenio rdm-records fixtures`` and ``add-to-fixture``.

A :class:`ModelRecordFixtures` is created automatically for every registered
model, except the models that invenio handles itself (see :data:`INVENIO_MODELS`),
reading the records to create from ``<model-code>.yaml`` (or ``<model-code>.json``
if there is no YAML file) in the instance's ``app_data`` folder.

Usage
-----

To ship sample records for a ``datasets`` model, lay out the instance's
``app_data`` folder (``<instance_path>/app_data``) like this:

.. code-block:: text

    app_data/
        datasets.yaml         # named after the model's code
        files/
            data.csv          # referenced from datasets.yaml

``datasets.yaml`` is a list of records in the same shape as the model's REST API
input (``datasets.json`` with the same content as JSON works too):

.. code-block:: yaml

    - id: abcde-12345            # optional, see below
      metadata:
        title: My first dataset
      files:
        enabled: false           # a metadata-only record
    - id: fghij-67890
      community: my-community    # optional, slug of the community
      metadata:
        title: A dataset with files
      files:
        entries:
          - key: data.csv
            path: files/data.csv # local file, relative to app_data
            size: 1024
            checksum: md5:0cc175b9c0f1b6a831c399e269772661
          - key: remote.pdf
            size: 52341
            checksum: md5:92eb5ffee6ae2fec3ad71c777531578f
            transfer:
              type: F            # downloaded by the fixture
              url: https://example.org/remote.pdf

and is loaded with:

.. code-block:: console

    invenio rdm-records add-to-fixture datasets

After that, ``abcde-12345`` and ``fghij-67890`` are published records of the
``datasets`` model. Editing the YAML (or ``files/data.csv``) and running the
command again updates them.

Records
-------

* ``id`` (optional) is used as the pid of the created record. If a record with
  this ``id`` already exists, it is updated instead, so the fixture can be
  re-run to bring the records up to date. Without ``id``, a new record with a
  generated pid is created on every run.
* Records of draft-enabled models are published after they are created or
  updated.
* ``community`` (optional) is the slug (or id) of a community the record is
  added to after it is published. It is added directly, without a community
  inclusion request, and becomes the record's default community if it has
  none. A record already in the community is left as is. The model's records
  must be RDM-based (have ``parent.communities``).
* ``files.enabled`` defaults to ``true`` when ``files.entries`` are given. A
  draft-enabled model with files enabled by default needs ``enabled: false``
  for records without files, otherwise they can not be published.

Referencing files
-----------------

Each item of ``files.entries`` has a ``key`` (the file name in the record),
``size`` (in bytes), ``checksum`` (``md5:<hex>``, e.g. from ``md5sum``) and
optional ``metadata``, plus one of:

* ``path`` - a local file, relative to the ``app_data`` folder (e.g.
  ``app_data/files/data.csv`` above). Its content is uploaded by the fixture.
* ``transfer`` with ``type: F`` and ``url`` - the file is downloaded by the
  fixture (not by a background task), so the record can be published right away.
* any other ``transfer`` (e.g. ``type: R`` for a remote file served from its
  ``url``) - passed to the file service as is.

Always give ``size`` and ``checksum``: on re-run, a file is only re-transferred
when they differ from the recorded ones, so a remote or fetched file without
them is downloaded again on every run. (For a local file they are computed from
its content, so the comparison stays correct even if the entry is out of date.)
Recorded files missing from the entry are deleted.

Loading the data
----------------

* ``invenio rdm-records fixtures`` loads all of them after the RDM fixtures.
* ``invenio rdm-records add-to-fixture <model-code>`` loads just one model's
  fixture; an unknown name falls through to the RDM vocabulary reload.

With ``INVENIO_LAZY_FIXTURES=on`` in the environment, each record is created in
a celery worker instead (the worker needs the same ``app_data`` folder). A record
that fails to load is logged as an error and the remaining records are loaded.

To read the model fixtures (and the files they reference) from another folder,
set ``OAREPO_FIXTURES_FOLDER`` in ``invenio.cfg`` or the environment, e.g.:

.. code-block:: console

    INVENIO_OAREPO_FIXTURES_FOLDER=/path/to/sample-data invenio rdm-records add-to-fixture datasets

Only the fixtures described here (and custom loaders below) use this folder; the
RDM vocabulary fixtures are always read from ``<instance_path>/app_data``.

Custom loaders
--------------

A model can override the default fixture by registering a callable under the
``oarepo.fixtures`` entry-point group, named after the model's code:

    [project.entry-points."oarepo.fixtures"]
    mst-records = "common.samples.fixtures:load_mst_records"

The callable is called as ``loader(identity, app_data_folder)`` and is run by
both commands above in place of the default fixture.

"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from flask import Flask, current_app
from invenio_base.utils import entry_points
from invenio_rdm_records.fixtures import FixturesEngine
from invenio_rdm_records.fixtures.fixture import FixtureMixin

from oarepo_runtime.fixtures.tasks import load_fixture_entry
from oarepo_runtime.proxies import current_runtime

if TYPE_CHECKING:
    from importlib.metadata import EntryPoint

FIXTURES_GROUP = "oarepo.fixtures"

# Models provided and loaded by invenio itself (the default vocabularies plus
# invenio's own users/communities/records). Invenio ships its own fixtures for
# these, so no record fixture is created for them.
INVENIO_MODELS = frozenset(
    {
        "vocabularies",
        "affiliations",
        "funders",
        "awards",
        "names",
        "subjects",
        "users",
        "communities",
        "records",
    }
)

_original_run = FixturesEngine.run
_original_add_to = FixturesEngine.add_to


class ModelRecordFixtures(FixtureMixin):
    """Read ``<model-code>.yaml`` or ``.json`` and hand each entry to :func:`load_fixture_entry`.

    See the module docstring for the file format.
    """

    def __init__(self, model_code: str, app_data_folder: Path) -> None:
        """Initialize the fixture for the model with the given code."""
        self._model_code = model_code
        self._app_data_folder = app_data_folder
        # JSON is valid YAML, so FixtureMixin's yaml.safe_load reads both
        filename = next(
            (name for name in (f"{model_code}.yaml", f"{model_code}.json") if (app_data_folder / name).exists()),
            f"{model_code}.yaml",
        )
        super().__init__([app_data_folder], filename)

    def create(self, entry: dict[str, Any]) -> None:
        """Load the entry in a celery worker if ``INVENIO_LAZY_FIXTURES`` is on, otherwise right away."""
        # resolved, so a relative folder does not depend on the worker's working directory
        args = (self._model_code, str(self._app_data_folder.resolve()), entry)
        if os.environ.get("INVENIO_LAZY_FIXTURES", "").lower() in {"1", "true", "on", "yes"}:
            load_fixture_entry.delay(*args)
        else:
            load_fixture_entry(*args)


def _fixtures_folder() -> Path:
    """Return ``OAREPO_FIXTURES_FOLDER`` if configured, otherwise the instance's ``app_data`` folder."""
    folder = current_app.config.get("OAREPO_FIXTURES_FOLDER")
    return Path(folder) if folder else Path(current_app.instance_path) / "app_data"


def _call(_engine: FixturesEngine, ep: EntryPoint) -> None:
    ep.load()(search_paths=[_fixtures_folder()], filename=ep.name + ".yaml").load()


def _model_fixtures() -> dict[str, ModelRecordFixtures]:
    """Build the default fixtures for every model not overridden by an entry point."""
    overridden = {ep.name for ep in entry_points(group=FIXTURES_GROUP)}
    app_data_folder = _fixtures_folder()
    return {
        model.code: ModelRecordFixtures(model.code, app_data_folder)
        for model in current_runtime.models.values()
        if model.code not in overridden and model.code not in INVENIO_MODELS
    }


def _run(self: FixturesEngine) -> None:
    _original_run(self)
    for ep in entry_points(group=FIXTURES_GROUP):
        _call(self, ep)
    for fixture in _model_fixtures().values():
        fixture.load()


def _add_to(self: FixturesEngine, fixture: str) -> None:
    eps = [ep for ep in entry_points(group=FIXTURES_GROUP) if ep.name == fixture]
    if eps:
        for ep in eps:
            _call(self, ep)
        return
    model_fixtures = _model_fixtures()
    if fixture in model_fixtures:
        model_fixtures[fixture].load()
        return
    _original_add_to(self, fixture)


def setup_fixtures(_app: Flask) -> None:
    """Install the patch (idempotent)."""
    FixturesEngine.run = _run
    FixturesEngine.add_to = _add_to
