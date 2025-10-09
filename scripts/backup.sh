#!/bin/bash
set -e

BACKUP_DIR=${BACKUP_DIR:-"./backups"}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "💾 Creating backup..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
echo "🗄️  Backing up PostgreSQL..."
docker-compose exec -T postgres pg_dump -U postgres eventslake > "$BACKUP_DIR/postgres_$TIMESTAMP.sql"

# Backup Redis
echo "💾 Backing up Redis..."
docker-compose exec -T redis redis-cli --rdb /data/dump.rdb
docker cp event-mgmt-mvp-redis:/data/dump.rdb "$BACKUP_DIR/redis_$TIMESTAMP.rdb"

# Backup MinIO
echo "📦 Backing up MinIO..."
docker run --rm --network event-mgmt-mvp-network \
    -v $BACKUP_DIR:/backup \
    minio/mc:latest \
    cp --recursive minio/minio/eventslake /backup/minio_$TIMESTAMP

# Compress backups
echo "🗜️  Compressing backups..."
tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" \
    "$BACKUP_DIR/postgres_$TIMESTAMP.sql" \
    "$BACKUP_DIR/redis_$TIMESTAMP.rdb" \
    "$BACKUP_DIR/minio_$TIMESTAMP"

# Clean up individual files
rm -rf "$BACKUP_DIR/postgres_$TIMESTAMP.sql" \
    "$BACKUP_DIR/redis_$TIMESTAMP.rdb" \
    "$BACKUP_DIR/minio_$TIMESTAMP"

echo "✅ Backup created: backup_$TIMESTAMP.tar.gz"
