from base64 import b64encode
from pathlib import Path

import yaml

from oarepo_runtime.datastreams import BaseReader, StreamEntry
from oarepo_runtime.datastreams.types import StreamEntryFile
from oarepo_runtime.datastreams.writers.attachments_file import format_serial


class AttachmentsReaderMixin(BaseReader):
    def __init__(self, *, source=None, base_path=None, **kwargs):
        super().__init__(source=source, base_path=base_path, **kwargs)
        self.has_files = self.base_path and (self.base_path / "files").is_dir()

    def __iter__(self):
        """Iterate over records."""
        se: StreamEntry
        for idx, se in enumerate(self.iter_entries()):
            if self.has_files:
                file_path = (
                    self.base_path.joinpath("files", format_serial(idx + 1)) / "data"
                )
                if file_path.exists():
                    file_metadata = self.load_file_metadata(file_path)
                    for md in file_metadata:
                        se.files.append(
                            StreamEntryFile(
                                metadata=md,
                                content_url="data:"
                                + b64encode(
                                    (file_path / md["key"]).read_bytes()
                                ).decode("ascii"),
                            )
                        )
            yield se

    def load_file_metadata(self, file_path: Path):
        md = "metadata.yaml"
        while True:
            tested_md = "meta_" + md
            # meta_[A]metadata.yaml does not exist, so [A]metadata.yaml is the metadata file,
            # where A is (meta_)*
            if not (file_path / tested_md).exists():
                with open(file_path / md) as f:
                    return list(yaml.safe_load_all(f))
            md = tested_md

    def iter_entries(self):
        "Return an iterator of entries"
        return []
