#!/bin/sh
set -e

echo "==> Waiting for Postgres..."
while ! python -c "
import asyncio, asyncpg, os
async def check():
    url = os.environ['DATABASE_URL'].replace('+asyncpg','').replace('postgresql','postgres')
    conn = await asyncpg.connect(url.replace('postgres://','postgresql://'))
    await conn.close()
asyncio.run(check())
" 2>/dev/null; do
    sleep 1
done
echo "==> Postgres is ready"

echo "==> Running migrations..."
cd /app && alembic upgrade head

echo "==> Starting application..."
exec "$@"
