#!/usr/bin/env bash
set -e
WORKDIR="/c/Users/chris/social-affiliate"
cd "$WORKDIR"
TIMESTAMP=$(date -Iseconds)
LOG="$WORKDIR/logs/run-$TIMESTAMP.log"
mkdir -p "$WORKDIR/logs"

{
  echo "=== Run $TIMESTAMP ==="
} > "$LOG"

# Discovery - Use web tools via hermes? For now, placeholder
# In real run, Hermes agent will have performed web_search and web_extract
# Here we just commit any new content

if [ -d "$WORKDIR/content" ]; then
  NEW_FILES=$(find "$WORKDIR/content" -type f -name "*.md" -newer "$WORKDIR/.git/index" 2>/dev/null || true)
  if [ -n "$NEW_FILES" ]; then
    echo "New content files detected:" >> "$LOG"
    echo "$NEW_FILES" >> "$LOG"
    git add "$WORKDIR/content" "$WORKDIR/metrics.csv"
    git commit -m "auto: new affiliate reviews $(date -I)" >> "$LOG" 2>&1
    # Push would go here if remote exists
    echo "Committed" >> "$LOG"
  else
    echo "No new files" >> "$LOG"
  fi
else
  echo "No content dir" >> "$LOG"
fi
