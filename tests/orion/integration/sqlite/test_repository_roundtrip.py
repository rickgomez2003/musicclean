from pathlib import Path

from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.domain import (
    Album,
    Artist,
    AudioFile,
    Disc,
    Edition,
    Library,
    Recording,
    TrackAppearance,
)
from musicclean.orion.shared import ByteSize, Duration


def test_core_domain_round_trips_through_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"

    library = Library("Main Music")
    artist = Artist("Artist", sort_name="Artist")
    album = Album("Album")
    edition = Edition(
        album_id=album.id,
        release_label="Deluxe",
        media_format="FLAC",
        catalog_number="CAT-1",
        barcode="12345",
    )
    disc = Disc(edition_id=edition.id, position=1, title="Disc One")
    recording = Recording("Track", duration=Duration.from_seconds(123.456))
    appearance = TrackAppearance(
        disc_id=disc.id,
        recording_id=recording.id,
        position=1,
        title_override="Album Version",
    )
    audio_file = AudioFile(
        location=r"\\nas\music\track.flac",
        size=ByteSize(987654321),
        recording_id=recording.id,
    )

    with SqliteUnitOfWork(db_path) as uow:
        uow.libraries.save(library)
        uow.artists.save(artist)
        uow.albums.save(album)
        uow.editions.save(edition)
        uow.discs.save(disc)
        uow.recordings.save(recording)
        uow.track_appearances.save(appearance)
        uow.audio_files.save(audio_file)
        uow.commit()

    with SqliteUnitOfWork(db_path) as uow:
        assert uow.libraries.get(library.id) == library
        assert uow.artists.get(artist.id) == artist
        assert uow.albums.get(album.id) == album
        assert uow.editions.get(edition.id) == edition
        assert uow.discs.get(disc.id) == disc
        assert uow.recordings.get(recording.id) == recording
        assert uow.track_appearances.get(appearance.id) == appearance
        assert uow.audio_files.get(audio_file.id) == audio_file

        assert uow.editions.list_for_album(album.id) == (edition,)
        assert uow.discs.list_for_edition(edition.id) == (disc,)
        assert uow.track_appearances.list_for_disc(disc.id) == (appearance,)
        assert uow.track_appearances.list_for_recording(recording.id) == (appearance,)
        assert uow.audio_files.list_for_recording(recording.id) == (audio_file,)
