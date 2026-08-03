# Domain Model

- **Library** — managed collection and configured roots.
- **Artist** — credited creator or performer.
- **Album** — abstract release concept.
- **Edition** — specific published version.
- **Disc** — physical/logical carrier in an Edition.
- **Recording** — recorded performance independent of release/file.
- **TrackAppearance** — placement of a Recording on a Disc/Edition.
- **AudioFile** — concrete digital representation at a mutable location.
- **Evidence** — observation with provenance.
- **Knowledge** — versioned inferred fact supported by Evidence.
- **Decision** — explainable proposed action derived from Knowledge.

Stable identity must never be derived from a path.

```mermaid
erDiagram
 ALBUM ||--o{ EDITION : has
 EDITION ||--o{ DISC : contains
 DISC ||--o{ TRACK_APPEARANCE : orders
 RECORDING ||--o{ TRACK_APPEARANCE : appears_as
 RECORDING ||--o{ AUDIO_FILE : represented_by
 AUDIO_FILE ||--o{ EVIDENCE : observed_by
 EVIDENCE }o--o{ KNOWLEDGE : supports
 KNOWLEDGE }o--o{ DECISION : informs
```
