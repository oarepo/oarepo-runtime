import sys

import click
from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.services.uow import unit_of_work
from oarepo_runtime.cli import index
from oarepo_runtime.cli.index import  model_records_generator
from oarepo_runtime.datastreams.utils import get_file_service_for_record_service


def reindex():
    services = current_service_registry._services.keys()

    for service_id in services:
        service = current_service_registry.get(service_id)
        record_class = getattr(service.config, "record_cls", None)

        id_generators = []

        if record_class and hasattr(service, "indexer"):
            try:
                id_generators.append(model_records_generator(record_class))
            except Exception as e:
                click.secho(
                    f"Could not get record ids for {service_id}, exception {e}",
                    file=sys.stderr,
                )

        draft_class = getattr(service.config, "draft_cls", None)

        if draft_class and hasattr(service, "indexer"):
            try:
                id_generators.append(model_records_generator(draft_class))
            except Exception as e:
                click.secho(
                    f"Could not get draft record ids for {service_id}, exception {e}",
                    file=sys.stderr,
                )
        count = 0
        for gen in id_generators:
            for record in gen:
                service.indexer.index(record)
                count += 1
        if count:
            service.indexer.refresh()





class FeaturedFileServiceMixin:
    @unit_of_work()
    def commit_file(self, identity, id_, file_key, uow=None):

        # """Commit a file upload.
        #
        # :raises FileKeyNotFoundError: If the record has no file for the ``file_key``
        # """
        # record = self._get_record(id_, identity, "commit_files", file_key=file_key)
        reindex()


