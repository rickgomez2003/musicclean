from __future__ import annotations

from collections.abc import Iterable

from musicclean.orion.domain import Album, Artist, AudioFile, Edition, Library, Recording
from musicclean.orion.shared import ByteSize, EntityId


class InMemoryLibraryRepository:
    def __init__(self) -> None:
        self.items: dict[EntityId, Library] = {}

    def get(self, library_id: EntityId) -> Library | None:
        return self.items.get(library_id)

    def list_all(self) -> tuple[Library, ...]:
        return tuple(self.items.values())

    def save(self, library: Library) -> None:
        self.items[library.id] = library


class InMemoryArtistRepository:
    def __init__(self) -> None:
        self.items: dict[EntityId, Artist] = {}

    def get(self, artist_id: EntityId) -> Artist | None:
        return self.items.get(artist_id)

    def find_by_name(self, name: str) -> tuple[Artist, ...]:
        return tuple(item for item in self.items.values() if item.name == name)

    def save(self, artist: Artist) -> None:
        self.items[artist.id] = artist


class InMemoryAlbumRepository:
    def __init__(self) -> None:
        self.items: dict[EntityId, Album] = {}

    def get(self, album_id: EntityId) -> Album | None:
        return self.items.get(album_id)

    def find_by_title(self, title: str) -> tuple[Album, ...]:
        return tuple(item for item in self.items.values() if item.title == title)

    def save(self, album: Album) -> None:
        self.items[album.id] = album


class InMemoryEditionRepository:
    def __init__(self) -> None:
        self.items: dict[EntityId, Edition] = {}

    def get(self, edition_id: EntityId) -> Edition | None:
        return self.items.get(edition_id)

    def list_for_album(self, album_id: EntityId) -> tuple[Edition, ...]:
        return tuple(item for item in self.items.values() if item.album_id == album_id)

    def save(self, edition: Edition) -> None:
        self.items[edition.id] = edition


class InMemoryRecordingRepository:
    def __init__(self) -> None:
        self.items: dict[EntityId, Recording] = {}

    def get(self, recording_id: EntityId) -> Recording | None:
        return self.items.get(recording_id)

    def find_by_title(self, title: str) -> tuple[Recording, ...]:
        return tuple(item for item in self.items.values() if item.title == title)

    def save(self, recording: Recording) -> None:
        self.items[recording.id] = recording


class InMemoryAudioFileRepository:
    def __init__(self) -> None:
        self.items: dict[EntityId, AudioFile] = {}

    def get(self, audio_file_id: EntityId) -> AudioFile | None:
        return self.items.get(audio_file_id)

    def get_by_location(self, location: str) -> AudioFile | None:
        return next((item for item in self.items.values() if item.location == location), None)

    def list_for_recording(self, recording_id: EntityId) -> tuple[AudioFile, ...]:
        return tuple(item for item in self.items.values() if item.recording_id == recording_id)

    def save(self, audio_file: AudioFile) -> None:
        self.items[audio_file.id] = audio_file

    def save_many(self, audio_files: Iterable[AudioFile]) -> None:
        for audio_file in audio_files:
            self.save(audio_file)


def test_repository_contracts_support_domain_operations() -> None:
    library_repo = InMemoryLibraryRepository()
    artist_repo = InMemoryArtistRepository()
    album_repo = InMemoryAlbumRepository()
    edition_repo = InMemoryEditionRepository()
    recording_repo = InMemoryRecordingRepository()
    audio_repo = InMemoryAudioFileRepository()

    library = Library("Main")
    artist = Artist("Artist")
    album = Album("Album")
    edition = Edition(album_id=album.id)
    recording = Recording("Track")
    audio_file = AudioFile(
        location="/music/track.flac",
        size=ByteSize(123),
        recording_id=recording.id,
    )

    library_repo.save(library)
    artist_repo.save(artist)
    album_repo.save(album)
    edition_repo.save(edition)
    recording_repo.save(recording)
    audio_repo.save(audio_file)

    assert library_repo.get(library.id) == library
    assert artist_repo.find_by_name("Artist") == (artist,)
    assert album_repo.find_by_title("Album") == (album,)
    assert edition_repo.list_for_album(album.id) == (edition,)
    assert recording_repo.find_by_title("Track") == (recording,)
    assert audio_repo.list_for_recording(recording.id) == (audio_file,)
