from musicclean.orion.ports import MetadataParser, MetadataProvider, MetadataSnapshot


def test_metadata_provider_is_protocol() -> None:
    assert getattr(MetadataProvider, "_is_protocol", False) is True


def test_metadata_snapshot_defaults_are_safe() -> None:
    snapshot = MetadataSnapshot()

    assert snapshot.parser is MetadataParser.UNKNOWN
    assert snapshot.parser_warning is None
    assert snapshot.has_artwork is False
