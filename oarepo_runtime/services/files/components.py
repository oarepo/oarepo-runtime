import mimetypes
import os

from invenio_records_resources.services.files.components import FileServiceComponent
from marshmallow.exceptions import ValidationError


class AllowedFileTypesComponent(FileServiceComponent):
    def guess_content_type(self, filename: str | None) -> str | None:
        if filename:
            return mimetypes.guess_type(filename)[0] or "application/octet-stream"
        return None

    @property
    def allowed_mimetypes(self):
        """Returns files attribute (field) key."""
        return getattr(self.service.config, "allowed_mimetypes", [])

    def guess_extension(self, file, mimetype):
        """File extension."""
        # The ``ext`` property is used to in search to aggregate file types, and we want e.g. both ``.jpeg`` and
        # ``.jpg`` to be aggregated under ``.jpg``
        ext_guessed = mimetypes.guess_extension(mimetype)

        # Check if a valid extension is guessed and it's not the default mimetype
        if ext_guessed is not None and mimetype != "application/octet-stream":
            return ext_guessed[1:]

        # Support non-standard file extensions that cannot be guessed
        _, ext = os.path.splitext(file)
        if ext and len(ext) <= 5:
            return ext[1:].lower()

        if ext_guessed:
            return ext_guessed[1:]

    @property
    def allowed_extensions(self):
        """Returns files attribute (field) key."""
        return getattr(self.service.config, "allowed_extensions", [])

    def init_files(self, identity, id_, data, uow=None):
        """Initialize the file upload for the record."""
        list_files = list(data.files.entries)

        for file in list_files:
            allowed_type = self.guess_content_type(file)
            allowed_ext = self.guess_extension(file, allowed_type)
            if (
                len(self.allowed_mimetypes) > 0
                and allowed_type not in self.allowed_mimetypes
            ):
                raise ValidationError(
                    f"Mimetype not supported, supported mimetypes: {self.allowed_mimetypes}"
                )
            elif (
                len(self.allowed_extensions) > 0
                and allowed_ext not in self.allowed_extensions
            ):
                raise ValidationError(
                    f"Extension not supported, supported extensions: {self.allowed_extensions}"
                )
