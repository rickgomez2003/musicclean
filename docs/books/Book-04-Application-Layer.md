# Book 04 — Application Layer

**Status:** Active specification

Current use cases:
- CreateLibrary
- RegisterAudioFile
- ListAlbumEditions
- SynchronizeFilesystem

Filesystem synchronization determines **what changed**, not **what the media
contains**. Metadata, hashing, fingerprinting, artwork, and audio analysis are
downstream responsibilities.
