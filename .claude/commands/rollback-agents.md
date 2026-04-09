# Rollback Agent Patches

Undo all command patches applied by `/generate-agents` and optionally remove generated agent files.

## Process

### 1. Read Patch Registry

Read `.claude/agents/_patches.json`. If the file doesn't exist or is empty, report "No patches found — nothing to rollback" and stop.

### 2. Display Current Patches

Present the list of patches:
```
## Current Agent Patches

| Command | Hook ID | Agent | Phase |
|---------|---------|-------|-------|
| [from _patches.json] |
```

Ask: "What would you like to do?
**[1]** Remove all command patches (restore original commands)
**[2]** Select specific patches to remove
**[3]** Remove patches AND delete all agent files
**[4]** Cancel"

**HALT — wait for user selection.**

### 3. Remove Patches

For each patch to remove:
1. Read the target command file
2. Find the sentinel block: `<!-- AGENT_HOOK:start:{hook-id} -->` through `<!-- AGENT_HOOK:end:{hook-id} -->`
3. Remove the entire sentinel block (including the comment markers themselves)
4. Remove any resulting blank line clusters (keep at most one blank line between sections)
5. Write the cleaned file

### 4. Update Registry

- If all patches removed: delete `_patches.json`
- If some patches remain: update `_patches.json` to reflect only remaining patches

### 5. Handle Agent Files (Option 3 only)

If user chose Option 3:
1. List all folders in `.claude/agents/` (excluding `_manifest.json` and `_patches.json`)
2. Confirm: "This will permanently delete these agent folders: [list]. Proceed? [yes/no]"
3. If confirmed, delete the agent folders, `_manifest.json`, and `_patches.json`
4. If `.claude/agents/` is now empty, remove the directory

### 6. Commit

1. Stage all modified/deleted files explicitly by name
2. Commit: `"chore: rollback agent patches"`
3. Report what was done:
```
## Rollback Complete

### Patches Removed
- [list commands restored]

### Agent Files
- [kept / deleted based on choice]

### Commands Restored
All patched commands now operate with their original inline behavior.
To regenerate agents, run `/generate-agents`.
```

## Important Rules
- Only remove content within sentinel markers — never modify code outside them
- Always stage files explicitly — never `git add .` or `git add -A`
- Confirm before deleting agent files — patches can be removed independently
- If a sentinel block is not found in a command file (manually removed?), log a warning and continue
