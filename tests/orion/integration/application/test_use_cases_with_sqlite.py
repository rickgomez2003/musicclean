from pathlib import Path

import pytest

from musicclean.orion.adapters.sqlite import SqliteUnitOfWork
from musicclean.orion.application import (
    ConflictError,
    CreateLibrary,
    ListAlbumEditions,
    NotFoundError,
    RegisterAudioFile,
    create_library,
    list_album_editions,
    register_audio_file,
)
from musicclean.orion.domain import Album, Edition, Recording


def _factory(db_path: Path):
    return lambda: SqliteUnitOfWork(db_path)


def test_create_library_persists_and_rejects_case_insensitive_duplicate(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "orion.db"
    factory = _factory(db_path)

    created = create_library(CreateLibrary("Main Music"), factory)

    with SqliteUnitOfWork(db_path) as uow:
        assert uow.libraries.get(created.id) == created

    with pytest.raises(ConflictError):
        create_library(CreateLibrary("main music"), factory)


def test_register_audio_file_is_idempotent_by_location(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    factory = _factory(db_path)

    first = register_audio_file(
        RegisterAudioFile(location="/music/track.flac", size_bytes=100),
        factory,
    )
    second = register_audio_file(
        RegisterAudioFile(location="/music/track.flac", size_bytes=200),
        factory,
    )

    assert second.id == first.id
    assert second.size.bytes == 200


def test_register_audio_file_validates_recording_reference(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    factory = _factory(db_path)
    recording = Recording("Track")

    with SqliteUnitOfWork(db_path) as uow:
        uow.recordings.save(recording)
        uow.commit()

    audio_file = register_audio_file(
        RegisterAudioFile(
            location="/music/track.flac",
            size_bytes=300,
            recording_id=recording.id,
        ),
        factory,
    )
    assert audio_file.recording_id == recording.id


def test_register_audio_file_rejects_unknown_recording(tmp_path: Path) -> None:
    from musicclean.orion.shared import EntityId

    db_path = tmp_path / "orion.db"
    with pytest.raises(NotFoundError):
        register_audio_file(
            RegisterAudioFile(
                location="/music/track.flac",
                size_bytes=300,
                recording_id=EntityId.new(),
            ),
            _factory(db_path),
        )


def test_list_album_editions_queries_existing_album(tmp_path: Path) -> None:
    db_path = tmp_path / "orion.db"
    factory = _factory(db_path)
    album = Album("Album")
    edition = Edition(album_id=album.id, release_label="Deluxe")

    with SqliteUnitOfWork(db_path) as uow:
        uow.albums.save(album)
        uow.editions.save(edition)
        uow.commit()

    assert list_album_editions(ListAlbumEditions(album.id), factory) == (edition,)


def test_list_album_editions_rejects_unknown_album(tmp_path: Path) -> None:
    from musicclean.orion.shared import EntityId

    db_path = tmp_path / "orion.db"
    with pytest.raises(NotFoundError):
        list_album_editions(ListAlbumEditions(EntityId.new()), _factory(db_path))
