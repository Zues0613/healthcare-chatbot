#!/bin/bash
# Setup script for Prisma

set -e

echo "Setting up Prisma..."

# Navigate to API directory
cd "$(dirname "$0")/.."

# Check if schema file exists
if [ ! -f "prisma/schema.prisma" ]; then
    echo "ERROR: Schema file not found at prisma/schema.prisma"
    exit 1
fi

# Generate Prisma client
echo "1. Generating Prisma client..."
prisma generate --schema prisma/schema.prisma

# Check if database URL is set
if [ -z "$NEON_DB_URL" ]; then
    echo "WARNING: NEON_DB_URL not set. Database connection cannot be tested."
    echo "Set NEON_DB_URL in your .env file to test the connection."
else
    echo "✓ NEON_DB_URL is set"
    
    # Push schema to database
    echo "2. Pushing schema to database..."
    prisma db push --schema prisma/schema.prisma --accept-data-loss
fi

echo "✓ Prisma setup complete!"

