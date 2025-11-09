#!/bin/sh
set -e
# Xtension Bot Docker Entrypoint: ownership/permissions automation

# Use PUID/PGID from Docker Compose, default to 1000 if unset
PUID=${PUID:-1000}
PGID=${PGID:-1000}

echo "Starting Xtension Bot with UID:GID $PUID:$PGID"

# Ensure botgroup exists for the given GID
if ! getent group botgroup >/dev/null; then
    addgroup -g "$PGID" botgroup
fi

# Ensure botuser exists for the given UID
if ! getent passwd botuser >/dev/null; then
    adduser -D -u "$PUID" -G botgroup botuser
fi

# Guarantee permissions on all app directories (add /app/downloads explicitly)
for dir in /app/sessions /app/data /app/plugins /app/logs /app/downloads; do
    [ -d "$dir" ] && chown -R "$PUID":"$PGID" "$dir" 2>/dev/null || true
done

# Run the bot as the correct user/group
exec su-exec "$PUID":"$PGID" "$@"