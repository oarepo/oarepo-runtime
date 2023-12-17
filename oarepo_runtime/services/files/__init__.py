try:
    from invenio_records_resources.services.records.components import (
        FilesOptionsComponent as FilesComponent,
    )
except ImportError:
    from invenio_records_resources.services.records.components import FilesComponent

__all__ = ("FilesComponent",)
