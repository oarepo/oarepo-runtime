from oarepo_runtime.records.systemfields.selectors import (
    FilteredSelector,
    MultiSelector,
    PathSelector,
)


def test_filtered_selector():
    data = {
        "metadata": {
            "creators": [
                {
                    "name": "hugo",
                    "affiliations": ["uni1", "uni2"],
                    "nameType": "personal",
                },
                {"name": "uni3", "nameType": "organizational"},
                {
                    "name": "andrej",
                    "nameType": "personal",
                },
            ]
        }
    }

    selector = FilteredSelector(
        PathSelector("metadata.creators", "metadata.contributors"),
        filter=lambda x: x["nameType"] == "personal",
        projection="affiliations",
    )

    result = selector.select(data)
    assert result == ["uni1", "uni2"]


def test_filtered_selector_function_projection():
    data = {
        "metadata": {
            "creators": [
                {
                    "name": "hugo",
                    "affiliations": ["uni1", "uni2"],
                    "nameType": "personal",
                },
                {"name": "uni3", "nameType": "organizational"},
                {
                    "name": "andrej",
                    "nameType": "personal",
                },
            ]
        }
    }

    selector = FilteredSelector(
        PathSelector("metadata.creators", "metadata.contributors"),
        filter=lambda x: x["nameType"] == "personal",
        projection=lambda x: x["name"].capitalize(),
    )

    result = selector.select(data)
    assert result == ["Hugo", "Andrej"]


def test_multiselector():
    data = {
        "metadata": {
            "creators": [
                {
                    "name": "hugo",
                    "affiliations": ["uni1", "uni2"],
                    "nameType": "personal",
                },
                {"name": "uni3", "nameType": "organizational"},
                {
                    "name": "andrej",
                    "nameType": "personal",
                },
            ]
        }
    }

    selectors = [
        FilteredSelector(
            PathSelector("metadata.creators", "metadata.contributors"),
            filter=lambda x: x["nameType"] == "personal",
            projection="affiliations",
        ),
        FilteredSelector(
            PathSelector("metadata.creators", "metadata.contributors"),
            filter=lambda x: x["nameType"] == "organizational",
        ),
    ]

    selector = MultiSelector(*selectors)
    result = selector.select(data)
    assert result == ["uni1", "uni2", {"name": "uni3", "nameType": "organizational"}]
