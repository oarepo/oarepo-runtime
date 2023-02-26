from invenio_db import db
from invenio_records.models import RecordMetadataBase


class Records2Metadata(db.Model, RecordMetadataBase):
    """Model for Records2Record metadata."""

    __tablename__ = "records2_metadata"

    # Enables SQLAlchemy-Continuum versioning
    __versioned__ = {}
