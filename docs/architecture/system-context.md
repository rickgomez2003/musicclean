# System Context

```mermaid
flowchart LR
 User[Collector / Administrator] --> Apps[MusicClean Apps]
 Apps --> Core[Orion Core]
 Core --> FS[Local / NAS Filesystems]
 Core --> Tools[FFmpeg / FFprobe / Mutagen]
 Core --> Ext[MusicBrainz / Discogs / AcoustID]
 Core --> DB[(Persistence)]
```
