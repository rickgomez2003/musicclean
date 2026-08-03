"""Concrete SQLite repository implementations for Orion."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable

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
from musicclean.orion.shared import ByteSize, Duration, EntityId


def _entity_id(value: object) -> EntityId:
    return EntityId.parse(str(value))


class SqliteLibraryRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get(self, library_id: EntityId) -> Library | None:
        row = self._connection.execute(
            "SELECT id, name FROM orion_libraries WHERE id = ?",
            (str(library_id),),
        ).fetchone()
        return None if row is None else Library(id=_entity_id(row["id"]), name=str(row["name"]))

    def list_all(self) -> tuple[Library, ...]:
        rows = self._connection.execute(
            "SELECT id, name FROM orion_libraries ORDER BY name, id"
        ).fetchall()
        return tuple(Library(id=_entity_id(row["id"]), name=str(row["name"])) for row in rows)

    def save(self, library: Library) -> None:
        self._connection.execute(
            """
            INSERT INTO orion_libraries(id, name) VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET name = excluded.name
            """,
            (str(library.id), library.name),
        )


class SqliteArtistRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Artist:
        return Artist(
            id=_entity_id(row["id"]),
            name=str(row["name"]),
            sort_name=str(row["sort_name"]) if row["sort_name"] is not None else None,
        )

    def get(self, artist_id: EntityId) -> Artist | None:
        row = self._connection.execute(
            "SELECT id, name, sort_name FROM orion_artists WHERE id = ?",
            (str(artist_id),),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def find_by_name(self, name: str) -> tuple[Artist, ...]:
        rows = self._connection.execute(
            """
            SELECT id, name, sort_name
              FROM orion_artists
             WHERE name = ?
             ORDER BY id
            """,
            (name,),
        ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def save(self, artist: Artist) -> None:
        self._connection.execute(
            """
            INSERT INTO orion_artists(id, name, sort_name)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                sort_name = excluded.sort_name
            """,
            (str(artist.id), artist.name, artist.sort_name),
        )


class SqliteAlbumRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Album:
        return Album(id=_entity_id(row["id"]), title=str(row["title"]))

    def get(self, album_id: EntityId) -> Album | None:
        row = self._connection.execute(
            "SELECT id, title FROM orion_albums WHERE id = ?",
            (str(album_id),),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def find_by_title(self, title: str) -> tuple[Album, ...]:
        rows = self._connection.execute(
            "SELECT id, title FROM orion_albums WHERE title = ? ORDER BY id",
            (title,),
        ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def save(self, album: Album) -> None:
        self._connection.execute(
            """
            INSERT INTO orion_albums(id, title) VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET title = excluded.title
            """,
            (str(album.id), album.title),
        )


class SqliteEditionRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Edition:
        return Edition(
            id=_entity_id(row["id"]),
            album_id=_entity_id(row["album_id"]),
            release_label=(str(row["release_label"]) if row["release_label"] is not None else None),
            media_format=(str(row["media_format"]) if row["media_format"] is not None else None),
            catalog_number=(
                str(row["catalog_number"]) if row["catalog_number"] is not None else None
            ),
            barcode=str(row["barcode"]) if row["barcode"] is not None else None,
        )

    def get(self, edition_id: EntityId) -> Edition | None:
        row = self._connection.execute(
            "SELECT * FROM orion_editions WHERE id = ?",
            (str(edition_id),),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def list_for_album(self, album_id: EntityId) -> tuple[Edition, ...]:
        rows = self._connection.execute(
            "SELECT * FROM orion_editions WHERE album_id = ? ORDER BY id",
            (str(album_id),),
        ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def save(self, edition: Edition) -> None:
        self._connection.execute(
            """
            INSERT INTO orion_editions(
                id, album_id, release_label, media_format, catalog_number, barcode
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                album_id = excluded.album_id,
                release_label = excluded.release_label,
                media_format = excluded.media_format,
                catalog_number = excluded.catalog_number,
                barcode = excluded.barcode
            """,
            (
                str(edition.id),
                str(edition.album_id),
                edition.release_label,
                edition.media_format,
                edition.catalog_number,
                edition.barcode,
            ),
        )


class SqliteDiscRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Disc:
        return Disc(
            id=_entity_id(row["id"]),
            edition_id=_entity_id(row["edition_id"]),
            position=int(row["position"]),
            title=str(row["title"]) if row["title"] is not None else None,
        )

    def get(self, disc_id: EntityId) -> Disc | None:
        row = self._connection.execute(
            "SELECT * FROM orion_discs WHERE id = ?",
            (str(disc_id),),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def list_for_edition(self, edition_id: EntityId) -> tuple[Disc, ...]:
        rows = self._connection.execute(
            """
            SELECT * FROM orion_discs
             WHERE edition_id = ?
             ORDER BY position, id
            """,
            (str(edition_id),),
        ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def save(self, disc: Disc) -> None:
        self._connection.execute(
            """
            INSERT INTO orion_discs(id, edition_id, position, title)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                edition_id = excluded.edition_id,
                position = excluded.position,
                title = excluded.title
            """,
            (str(disc.id), str(disc.edition_id), disc.position, disc.title),
        )


class SqliteRecordingRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Recording:
        duration = Duration(int(row["duration_ms"])) if row["duration_ms"] is not None else None
        return Recording(
            id=_entity_id(row["id"]),
            title=str(row["title"]),
            duration=duration,
        )

    def get(self, recording_id: EntityId) -> Recording | None:
        row = self._connection.execute(
            "SELECT * FROM orion_recordings WHERE id = ?",
            (str(recording_id),),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def find_by_title(self, title: str) -> tuple[Recording, ...]:
        rows = self._connection.execute(
            "SELECT * FROM orion_recordings WHERE title = ? ORDER BY id",
            (title,),
        ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def save(self, recording: Recording) -> None:
        duration_ms = recording.duration.milliseconds if recording.duration else None
        self._connection.execute(
            """
            INSERT INTO orion_recordings(id, title, duration_ms)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                duration_ms = excluded.duration_ms
            """,
            (str(recording.id), recording.title, duration_ms),
        )


class SqliteTrackAppearanceRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @staticmethod
    def _from_row(row: sqlite3.Row) -> TrackAppearance:
        return TrackAppearance(
            id=_entity_id(row["id"]),
            disc_id=_entity_id(row["disc_id"]),
            recording_id=_entity_id(row["recording_id"]),
            position=int(row["position"]),
            title_override=(
                str(row["title_override"]) if row["title_override"] is not None else None
            ),
        )

    def get(self, track_appearance_id: EntityId) -> TrackAppearance | None:
        row = self._connection.execute(
            "SELECT * FROM orion_track_appearances WHERE id = ?",
            (str(track_appearance_id),),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def list_for_disc(self, disc_id: EntityId) -> tuple[TrackAppearance, ...]:
        rows = self._connection.execute(
            """
            SELECT * FROM orion_track_appearances
             WHERE disc_id = ?
             ORDER BY position, id
            """,
            (str(disc_id),),
        ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def list_for_recording(self, recording_id: EntityId) -> tuple[TrackAppearance, ...]:
        rows = self._connection.execute(
            """
            SELECT * FROM orion_track_appearances
             WHERE recording_id = ?
             ORDER BY disc_id, position, id
            """,
            (str(recording_id),),
        ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def save(self, track_appearance: TrackAppearance) -> None:
        self._connection.execute(
            """
            INSERT INTO orion_track_appearances(
                id, disc_id, recording_id, position, title_override
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                disc_id = excluded.disc_id,
                recording_id = excluded.recording_id,
                position = excluded.position,
                title_override = excluded.title_override
            """,
            (
                str(track_appearance.id),
                str(track_appearance.disc_id),
                str(track_appearance.recording_id),
                track_appearance.position,
                track_appearance.title_override,
            ),
        )


class SqliteAudioFileRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    @staticmethod
    def _from_row(row: sqlite3.Row) -> AudioFile:
        recording_id = _entity_id(row["recording_id"]) if row["recording_id"] is not None else None
        return AudioFile(
            id=_entity_id(row["id"]),
            recording_id=recording_id,
            location=str(row["location"]),
            size=ByteSize(int(row["size_bytes"])),
        )

    def get(self, audio_file_id: EntityId) -> AudioFile | None:
        row = self._connection.execute(
            "SELECT * FROM orion_audio_files WHERE id = ?",
            (str(audio_file_id),),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def get_by_location(self, location: str) -> AudioFile | None:
        row = self._connection.execute(
            "SELECT * FROM orion_audio_files WHERE location = ?",
            (location,),
        ).fetchone()
        return None if row is None else self._from_row(row)

    def list_for_recording(self, recording_id: EntityId) -> tuple[AudioFile, ...]:
        rows = self._connection.execute(
            """
            SELECT * FROM orion_audio_files
             WHERE recording_id = ?
             ORDER BY location, id
            """,
            (str(recording_id),),
        ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def save(self, audio_file: AudioFile) -> None:
        self._connection.execute(
            """
            INSERT INTO orion_audio_files(id, recording_id, location, size_bytes)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                recording_id = excluded.recording_id,
                location = excluded.location,
                size_bytes = excluded.size_bytes
            """,
            (
                str(audio_file.id),
                str(audio_file.recording_id) if audio_file.recording_id else None,
                audio_file.location,
                audio_file.size.bytes,
            ),
        )

    def save_many(self, audio_files: Iterable[AudioFile]) -> None:
        for audio_file in audio_files:
            self.save(audio_file)
