# Git-Safe File Operations

## The Problem

When moving or renaming files that are tracked by git, using regular `mv` or `rename` commands breaks the git history chain. Git will show the file as deleted and a new unrelated file created, losing all commit history.

## The Solution

**Always use `git mv` for tracked files** to preserve history.

## Quick Check Pattern

Before moving/renaming ANY file:

```bash
# Check if file is tracked
git ls-files --error-unmatch <filename>

# If exit code 0 → file is tracked, use git mv
# If exit code non-zero → file is untracked, regular mv is fine
```

## Helper Script

Use the provided helper script that does this automatically:

```bash
./scripts/git_safe_move.sh <source> <destination>
```

**What it does:**
1. Checks if source file exists
2. Checks if file is tracked by git
3. If tracked → uses `git mv` (preserves history)
4. If untracked → uses regular `mv` (no history to preserve)
5. Creates destination directories if needed
6. Provides clear feedback

## Examples

### Single File Rename

```bash
# BAD (if tracked)
mv case_01.json trigger.json

# GOOD
git mv case_01.json trigger.json

# BEST (automatic check)
./scripts/git_safe_move.sh case_01.json trigger.json
```

### Move to Subdirectory

```bash
# BAD (if tracked)
mkdir -p aml/case_01
mv case_01.json aml/case_01/trigger.json

# GOOD
mkdir -p aml/case_01
git mv case_01.json aml/case_01/trigger.json

# BEST (automatic check + mkdir)
./scripts/git_safe_move.sh case_01.json aml/case_01/trigger.json
```

### Bulk Rename in Loop

```bash
# BAD
for file in case_*.json; do
    mv "$file" "renamed_${file}"
done

# GOOD
for file in case_*.json; do
    # Check each file
    if git ls-files --error-unmatch "$file" >/dev/null 2>&1; then
        git mv "$file" "renamed_${file}"
    else
        mv "$file" "renamed_${file}"
    fi
done

# BEST
for file in case_*.json; do
    ./scripts/git_safe_move.sh "$file" "renamed_${file}"
done
```

## Verifying History Preservation

After using `git mv`, verify history is preserved:

```bash
# Check git recognizes the rename
git status --short
# Should show: R old_path -> new_path

# Check history follows through rename
git log --follow --oneline <new_path>
# Should show commits from before the rename

# After committing, verify with:
git log --follow <new_path>
```

## Real-World Example: AML Case Migration

**Initial mistake (May 18, 2026):**
```bash
# Used regular mv, lost history
mv case_01/case_01.json case_01/trigger.json
```

**Fix applied:**
```bash
# 1. Restore to git's expected state
mv case_01/trigger.json case_01/case_01.json

# 2. Use git mv to rename
git mv case_01/case_01.json case_01/trigger.json

# 3. Result: Full history preserved
git status --short
# R  tests/eval/gold_cases/case_01.json -> tests/eval/gold_cases/aml/case_01/trigger.json
```

## Best Practices

1. **Always check first**: `git ls-files --error-unmatch <file>`
2. **Use git mv for tracked files**: Preserves commit history
3. **Use the helper script**: Automates the check + correct command
4. **Verify after**: Check `git status` shows `R` not `D` + `??`
5. **Test with `git log --follow`**: Confirm history is intact

## Why This Matters

- **Code archaeology**: Can trace file history through renames
- **Blame/annotate**: `git blame` works correctly through renames
- **Bisect**: `git bisect` can track changes through renames
- **Refactoring confidence**: Safe to reorganize code structure
- **Audit trail**: Complete change history for compliance/debugging

## Common Pitfalls

### ❌ Wrong: Using IDE/Editor rename without git integration
Many IDEs rename files but don't use `git mv`. Always verify after IDE rename.

### ❌ Wrong: Using shell globs with mv
```bash
mv case_*.json archive/  # May break history for tracked files
```

### ✅ Right: Check each file in loop
```bash
for file in case_*.json; do
    ./scripts/git_safe_move.sh "$file" "archive/$file"
done
```

### ❌ Wrong: Assuming files are untracked
Even if YOU created the file, check if someone committed it before you rename.

### ✅ Right: Always check tracking status
```bash
git ls-files --error-unmatch <file> && echo "TRACKED" || echo "UNTRACKED"
```

## Integration with Workflows

### Pre-commit Hook (Optional)

Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Warn if files show as deleted + new instead of renamed
deleted=$(git diff --cached --diff-filter=D --name-only)
added=$(git diff --cached --diff-filter=A --name-only)

if [ -n "$deleted" ] && [ -n "$added" ]; then
    echo "⚠️  Warning: Detected deleted and added files"
    echo "   This might be a rename that should have used 'git mv'"
    echo "   Deleted: $deleted"
    echo "   Added: $added"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
```

## Summary

| Action | Command | Use When |
|--------|---------|----------|
| Check if tracked | `git ls-files --error-unmatch <file>` | Before any move/rename |
| Move tracked file | `git mv <old> <new>` | File in git, manual |
| Move any file (auto) | `./scripts/git_safe_move.sh <old> <new>` | Unsure if tracked |
| Verify rename | `git status --short` | After move, should show `R` |
| Check history | `git log --follow <new_path>` | Verify history intact |

**Golden Rule:** If unsure, use the helper script. It's always safe and does the right thing.
