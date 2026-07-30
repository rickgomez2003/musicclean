from musicclean.metadata import _first, _tag


def test_first_handles_common_tag_values() -> None:
    assert _first([" Artist ", "Other"]) == "Artist"
    assert _first(b"Album") == "Album"
    assert _first([]) is None


def test_tag_is_case_insensitive() -> None:
    tags = {"ALBUMARTIST": ["Example Artist"], "Title": ["Example Song"]}

    assert _tag(tags, "albumartist") == "Example Artist"
    assert _tag(tags, "title") == "Example Song"
