# MusicClean 0.5.0 — Album Intelligence

This release completes parser-reliability cleanup and introduces the first intelligence layer.

## New command

```powershell
musicclean albums --limit 50 --reasons
musicclean albums --artist "Led Zeppelin" --album "Led Zeppelin III" --reasons
```

Each album directory is treated as an edition and scored from 0–100 using lossless format coverage, metadata completeness, artwork, MusicBrainz IDs, sample rate, bit depth, track count, and metadata errors. Recommendations are Keep, Archive, Review, or Cleanup candidate. No files are moved or deleted.

## Roadmap scaffolding

The next releases will add acoustic fingerprinting, waveform/quality analysis, an interactive review UI, and transactional quarantine/undo. Destructive actions remain intentionally disabled until review and rollback are implemented.
