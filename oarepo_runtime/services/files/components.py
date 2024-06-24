import mimetypes
import os
from invenio_records_resources.services.files.components import FileServiceComponent

class FileTypeException(Exception):

    def __init__(self, message):
        super().__init__(message)

class FileTypesComponent(FileServiceComponent):

    def guess_content_type(self, filename: str | None) -> str | None:
        if filename:
            return mimetypes.guess_type(filename)[0] or "application/octet-stream"
        return None

    @property
    def mimetypes(self):
        """Returns files attribute (field) key."""
        return getattr(self.service.config, "allowed_mimetypes", [])

    def guess_extension(self, file, mimetype):
        """File extension."""
        # The ``ext`` property is used to in search to aggregate file types, and we want e.g. both ``.jpeg`` and
        # ``.jpg`` to be aggregated under ``.jpg``
        ext_guessed = mimetypes.guess_extension(mimetype)

        # Check if a valid extension is guessed and it's not the default mimetype
        if (
                ext_guessed is not None
                and mimetype != "application/octet-stream"
        ):
            return ext_guessed[1:]

        # Support non-standard file extensions that cannot be guessed
        _, ext = os.path.splitext(file)
        if ext and len(ext) <= 5:
            return ext[1:].lower()

        if ext_guessed:
            return ext_guessed[1:]

    @property
    def extensions(self):
        """Returns files attribute (field) key."""
        return getattr(self.service.config, "allowed_extensions", [])

    def init_files(self, identity, id_, data, uow=None):
        """Initialize the file upload for the record."""
        list_files = list(data.files.entries)

        for file in list_files:
            type = self.guess_content_type(file)
            ext = self.guess_extension(file, type)
            if len(self.mimetypes) > 0 and type not in self.mimetypes:
                raise FileTypeException(f"Mimetype not supported, supported mimetypes: {self.mimetypes}")
            elif len(self.extensions) > 0 and ext not in self.extensions:
                raise FileTypeException(f"Extension not supported, supported extensions: {self.extensions}")

