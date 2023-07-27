import os
from base64 import b64decode
from pathlib import Path

import yaml

from oarepo_runtime.datastreams import StreamEntry

from . import BaseWriter


class AttachmentWriter(BaseWriter):
    """
    Writes the files and its metadata into subdirectories.

    The path will be files/<record-id>/<file-id>/metadata.yaml for technical metadata
    and files/<record-id>/<file-id>/<key> for the data.

    If the data key is "metadata.yaml", then "metadata" will be placed to "metametadata.yaml"
    """

    def __init__(self, *, target, base_path=None, **kwargs):
        """Constructor.
        :param file_or_path: path of the output file.
        """
        super().__init__(**kwargs)
        self._grouping = 3
        self._min_padding = 3
        if base_path:
            self._dir = base_path.joinpath(target)
        else:
            self._dir = Path(target)

    def write(self, entry: StreamEntry, *args, **kwargs):
        """Writes the input stream entry using a given service."""
        """
        context looks like: {
            'serial_no': 2, 
            'files': [
            {'metadata': {'updated': '...', 'mimetype': 'image/png', 'storage_class': 'L', 'file_id': '', 
                          'links': {...}, 'size': 27, 'status': 'completed', 'version_id': '...', 
                          'bucket_id': '...', 'metadata': None, 'key': 'test.png', 
                          'checksum': 'md5:...', 'created': '...'}, 
                          'content': b'test file content: test.png'}]}
        """
        if 'serial_no' not in entry.context or not entry.context.get('files'):
            return entry

        dirname = self._dir.joinpath(format_serial(entry.context['serial_no'])) / 'data'
        dirname.mkdir(parents=True, exist_ok=False)
        file_keys = []
        files_metadata = []
        for fn_idx, fn in enumerate(entry.context['files']):
            md = {**fn['metadata']}
            content = b64decode(fn['content'])
            md.pop('storage_class', None)
            md.pop('file_id', None)
            md.pop('links', None)
            md.pop('status', None)
            md.pop('version_id', None)
            md.pop('bucket_id', None)
            key = md['key']
            file_keys.append(key)
            files_metadata.append(md)
            (dirname / key).write_bytes(content)
        metadata_key = "metadata.yaml"
        while metadata_key in file_keys:
            metadata_key = "meta_" + metadata_key
        with open(dirname / metadata_key, "w") as f:
            yaml.safe_dump_all(files_metadata, f)
        return entry


    def delete(self, stream_entry: StreamEntry):
        """noop"""

    def finish(self):
        """Finalizes writing"""

def format_serial(serial_no):
    grouping = 3
    min_padding = 3
    serial_no = str(serial_no)
    formatted_length = max(min_padding, len(serial_no))
    while formatted_length % grouping:
        formatted_length += 1
    padded_serial = serial_no.zfill(formatted_length)
    return os.sep.join([padded_serial[i:i+grouping] for i in range(0, len(padded_serial), grouping)])
