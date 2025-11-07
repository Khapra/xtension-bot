#!/bin/sh
set -e

# Default PUID/PGID if not set
PUID=${PUID:-1000}
PGID=${PGID:-1000}

echo "Starting Xtension Bot with UID:GID $PUID:$PGID"

# Create group if it doesn't exist
if ! getent group botgroup >/dev/null; then
    addgroup -g "$PGID" botgroup
fi

# Create user if it doesn't exist
if ! getent passwd botuser >/dev/null; then
    adduser -D -u "$PUID" -G botgroup botuser
fi

# Fix permissions on writable dirs
for dir in /app/sessions /app/data /app/plugins /app/logs; do
    [ -d "$dir" ] && chown -R "$PUID":"$PGID" "$dir" 2>/dev/null || true
done

# Run as correct user
exec su-exec "$PUID":"$PGID" "$@"