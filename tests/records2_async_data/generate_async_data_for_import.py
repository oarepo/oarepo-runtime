import sys
from pathlib import Path

import yaml

from oarepo_runtime.datastreams.writers.attachments_file import format_serial

#
# Generates data for asynchronous fixture load test
#


def dump_yaml(path: Path, data):
    with path.open("w") as f:
        if isinstance(data, list):
            yaml.safe_dump_all(data, f)
        else:
            yaml.safe_dump(data, f)


def dump_file(path: Path, seq: int, key: str, metadata, content):
    # limitation - only one file supported
    dirname = path / "files" / format_serial(seq) / "data"
    dirname.mkdir(parents=True, exist_ok=True)
    (dirname / key).write_bytes(content)
    metadata_key = "metadata.yaml"
    with open(dirname / metadata_key, "w") as f:
        yaml.safe_dump({**metadata, "key": key}, f)


def generate(outdir, count):
    if not outdir.exists():
        outdir.mkdir(parents=True)

    records = [
        {
            "metadata": {
                "title": f"pkg record {i}",
            }
        }
        for i in range(count)
    ]

    dump_yaml(outdir / "records.yaml", records)
    dump_yaml(
        outdir / "catalogue.yaml",
        {
            "records2": [
                {"source": "records.yaml"},
                {"service": "records2"},
                {"writer": "attachments_service", "service": "records2"},
            ]
        },
    )
    img = (Path(__file__).parent / "test.png").read_bytes()
    for rec_idx in range(1, len(records) + 1):
        dump_file(
            outdir,
            rec_idx,
            "test.png",
            {},
            img,
        )


if __name__ == "__main__":
    generate(outdir=Path(sys.argv[1]), count=int(sys.argv[2]))
