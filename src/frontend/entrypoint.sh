#!/bin/sh

# Runtime environment variable substitution for Vite builds
# This replaces placeholder values with actual environment variables

echo "🔧 Configuring frontend with runtime environment variables..."

# Default API URL if not provided
VITE_API_URL=${VITE_API_URL:-"http://localhost:8000"}

echo "📡 Setting VITE_API_URL to: $VITE_API_URL"

# Find all JS files and replace various localhost patterns
echo "🔍 Searching for files to update..."
find /usr/share/nginx/html -name "*.js" -type f | while read -r file; do
    echo "Processing: $file"
    # Replace various localhost patterns with quotes
    sed -i "s|\"http://localhost:8000\"|\"$VITE_API_URL\"|g" "$file"
    sed -i "s|'http://localhost:8000'|'$VITE_API_URL'|g" "$file"
    # Replace without quotes
    sed -i "s|http://localhost:8000|$VITE_API_URL|g" "$file"
    sed -i "s|https://localhost:8000|$VITE_API_URL|g" "$file"
    # Replace just the host part
    sed -i "s|localhost:8000|${VITE_API_URL#*://}|g" "$file"
    # Replace any environment variable fallbacks
    sed -i "s|VITE_API_URL.*||.*\"http://localhost:8000\"|VITE_API_URL||\"$VITE_API_URL\"|g" "$file"
    sed -i "s|https://placeholder-backend-url|$VITE_API_URL|g" "$file"
done

# Also check HTML files for any hardcoded URLs
find /usr/share/nginx/html -name "*.html" -type f | while read -r file; do
    echo "Processing HTML: $file"
    sed -i "s|http://localhost:8000|$VITE_API_URL|g" "$file"
    sed -i "s|https://localhost:8000|$VITE_API_URL|g" "$file"
done

echo "✅ Environment variables configured successfully"

# Verify the replacement worked
echo "🔍 Verifying replacements..."
REMAINING=$(find /usr/share/nginx/html -name "*.js" -o -name "*.html" | xargs grep -l "localhost:8000" 2>/dev/null | wc -l)
if [ "$REMAINING" -gt 0 ]; then
    echo "⚠️  WARNING: Still found localhost:8000 references in $REMAINING files"
    find /usr/share/nginx/html -name "*.js" -o -name "*.html" | xargs grep -l "localhost:8000" 2>/dev/null || true
else
    echo "✅ SUCCESS: No more localhost:8000 references found"
fi

echo "🚀 Starting nginx..."

# Start nginx
exec nginx -g "daemon off;"
