# MusicClean Sprint 4.3

Hotfix for high-sample-rate WavPack files that exceed Mutagen's WavPack sample-rate table.

## Changes

- Falls back to `ffprobe` when Mutagen cannot parse a valid audio container.
- Reads WavPack APEv2 tags separately when possible.
- Preserves technical properties including 384 kHz sample rate and 32-bit depth.
- Shows the primary Mutagen failure as a warning in `musicclean inspect`.
- Scanner metadata extraction now benefits from the same fallback.

## Requirement

`ffprobe.exe` must be available in PATH. The validation system already confirmed it is available.
