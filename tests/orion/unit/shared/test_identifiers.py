from uuid import UUID

from musicclean.orion.shared import EntityId


def test_entity_id_new_creates_uuid() -> None:
    entity_id = EntityId.new()

    assert isinstance(entity_id.value, UUID)
    assert str(entity_id) == str(entity_id.value)


def test_entity_id_parse_round_trips() -> None:
    original = EntityId.new()

    parsed = EntityId.parse(str(original))

    assert parsed == original
