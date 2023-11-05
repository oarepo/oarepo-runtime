import time

import click
from invenio_access.permissions import system_identity
from invenio_app.factory import create_api
from invenio_records_resources.proxies import current_service_registry


@click.command()
@click.argument("expected_count", type=int)
def check_async_data_loaded(expected_count):
    records_service = current_service_registry.get("records2")
    files_service = current_service_registry.get("records2_file")

    for i in range(30):
        search_result = records_service.search(system_identity)
        if search_result.total == expected_count:
            break
        print(f"So far got {search_result.total} records, waiting for {expected_count}")
        time.sleep(1)
    else:
        raise Exception("Did not get all records")


if __name__ == "__main__":
    api = create_api()
    with api.app_context():
        check_async_data_loaded()
