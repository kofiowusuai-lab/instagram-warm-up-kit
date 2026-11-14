# Updating without losing working accounts

The image pins AliasMode 0.1.0-beta.74 and its Linux archive SHA-256. Upgrade both values together only after obtaining the checksum from the official release and testing the new image. Do not make a 'latest' change silently.

Saved private scripts intentionally survive image updates. To apply a new source version, back up the existing script store and account volume, close AliasMode, and replace only the intended source using a version-aware migration or the app's Replace file control. The seeder does not overwrite user edits. Run regression and infrastructure checks afterwards; do not execute Instagram activities to validate an upgrade under the manual-only manager policy. Preserve the last working source in Git so it can be restored independently of profile state.

Original scripts are under `scripts/original/`; corrected preloaded copies are under `scripts/`. Never swap the originals back over the corrected copies merely to match the public library. Active mode has real external actions and is not executed by the current manual-only manager.
