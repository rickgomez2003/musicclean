"""Pure MusicClean Orion domain model.

The domain must not depend on concrete persistence, media parsers, network
clients, CLI frameworks, or UI frameworks.
"""

from musicclean.orion.domain.album import Album
from musicclean.orion.domain.artist import Artist
from musicclean.orion.domain.audio_file import AudioFile
from musicclean.orion.domain.disc import Disc
from musicclean.orion.domain.edition import Edition
from musicclean.orion.domain.library import Library
from musicclean.orion.domain.recording import Recording
from musicclean.orion.domain.track_appearance import TrackAppearance

__all__ = [
    "Album",
    "Artist",
    "AudioFile",
    "Disc",
    "Edition",
    "Library",
    "Recording",
    "TrackAppearance",
]
