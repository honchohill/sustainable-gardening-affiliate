#!/usr/bin/env bash
set -e
WORKDIR="C:/Users/chris/social-affiliate"
cd "$WORKDIR"
TIMESTAMP=$(date -Iseconds)
LOG="$WORKDIR/logs/run-$TIMESTAMP.log"

# Log the run
echo "[$TIMESTAMP] Published content" >> "$LOG"

# Commit new content via Git
git add content/
if git diff --cached --exit-code &>/dev/null; then
    echo "No new content to commit."
else
    git commit -m "[auto] New affiliate reviews"
    echo "[auto] Commited new reviews."
fi

# Generate and publish
hugo
rsync -r -p -t -v -z -e ssh "content/" "user@server:/var/www/site/"

# Log success
echo "[auto] Done. Published to site." >> "$LOG"
