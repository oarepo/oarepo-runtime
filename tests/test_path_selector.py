from oarepo_runtime.records.systemfields.selectors import (
    FilteredSelector,
    MultiSelector,
    PathSelector,
    getter,
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


def test_getter():
    data = {
        "creators": [
            {"name": "hugo", "affiliations": ["uni1", "uni2"], "nameType": "personal"},
            {"name": "uni3", "nameType": "organizational"},
        ]
    }

    result1 = list(getter(data, "creators?nameType=personal.affiliations".split(".")))
    result2 = list(getter(data, "creators?nameType=organizational".split(".")))
    result3 = list(getter(data, "creators".split(".")))
    result4 = list(getter(data, "creators.affiliations".split(".")))

    assert result1 == ["uni1", "uni2"]
    assert result2 == [{"name": "uni3", "nameType": "organizational"}]
    assert result3 == [
        {"name": "hugo", "affiliations": ["uni1", "uni2"], "nameType": "personal"},
        {"name": "uni3", "nameType": "organizational"},
    ]
    assert result4 == ["uni1", "uni2"]


def test_getter_more_complex():
    data = {
        "creators": [
            {
                "name": {
                    "u": {
                        "university": {"org": "cvut", "city": "prag"},
                        "type": "technical",
                    },
                    "v": "uni3",
                },
                "nameType": "organizational",
            },
            {
                "name": "hugo",
                "affiliations": [
                    {"institution": {"u": "uni1", "v": "uni2"}, "graduated": "yes"},
                    {"institution": {"u": "uni3", "v": "uni3"}, "graduated": "no"},
                ],
                "nameType": "personal",
            },
        ]
    }

    result0 = list(
        getter(
            data,
            "creators?nameType=personal.affiliations.institution?graduated=yes".split(
                "."
            ),
        )
    )

    result = list(
        getter(
            data,
            "creators?nameType=organizational.name.u?v=uni3.university?type=technical".split(
                "."
            ),
        )
    )

    result1 = list(
        getter(data, "creators?nameType=personal.affiliations?graduated=yes".split("."))
    )
    result2 = list(
        getter(
            data,
            "creators?nameType=personal.affiliations?graduated=yes.institution.u".split(
                "."
            ),
        )
    )
    result3 = list(
        getter(data, "creators?nameType=personal.affiliations.institution".split("."))
    )
    assert result == [{"org": "cvut", "city": "prag"}]
    assert result0 == [{"u": "uni3", "v": "uni3"}]
    assert result1 == [{"institution": {"u": "uni1", "v": "uni2"}, "graduated": "yes"}]
    assert result2 == ["uni1"]
    assert result3 == [{"u": "uni1", "v": "uni2"}, {"u": "uni3", "v": "uni3"}]
