import pytest

from musicclean.orion.domain import Album, Disc, Edition, Recording, TrackAppearance
from musicclean.orion.shared import DomainValidationError


def test_track_appearance_links_recording_to_disc() -> None:
    edition = Edition(album_id=Album("Album").id)
    disc = Disc(edition_id=edition.id, position=1)
    recording = Recording("Track")

    appearance = TrackAppearance(
        disc_id=disc.id,
        recording_id=recording.id,
        position=3,
        title_override=" Album Version ",
    )

    assert appearance.disc_id == disc.id
    assert appearance.recording_id == recording.id
    assert appearance.position == 3
    assert appearance.title_override == "Album Version"


@pytest.mark.parametrize("position", [0, -5])
def test_track_appearance_rejects_invalid_position(position: int) -> None:
    edition = Edition(album_id=Album("Album").id)
    disc = Disc(edition_id=edition.id, position=1)
    recording = Recording("Track")

    with pytest.raises(DomainValidationError):
        TrackAppearance(disc_id=disc.id, recording_id=recording.id, position=position)
