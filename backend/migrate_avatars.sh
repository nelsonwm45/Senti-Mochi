#!/bin/bash
# Script to migrate all avatars from finance-documents to avatars bucket

echo "🔄 Migrating avatars to correct bucket..."

# Get all users with avatar_url in finance-documents bucket
docker compose exec db psql -U user -d finance_db -t -c "
SELECT email, avatar_url 
FROM users 
WHERE avatar_url LIKE '%finance-documents%'
" | while IFS='|' read email avatar_url; do
    # Trim whitespace
    email=$(echo "$email" | xargs)
    avatar_url=$(echo "$avatar_url" | xargs)
    
    if [ -n "$avatar_url" ]; then
        # Extract the file path from URL
        file_path=$(echo "$avatar_url" | sed 's|http://localhost:9000/finance-documents/||')
        
        echo "📦 Migrating avatar for: $email"
        echo "   From: finance-documents/$file_path"
        echo "   To: avatars/$file_path"
        
        # Copy file to avatars bucket
        docker compose exec minio sh -c "mc alias set local http://localhost:9000 minioadmin minioadmin > /dev/null 2>&1 && mc cp local/finance-documents/$file_path local/avatars/$file_path" || echo "⚠️  Failed to copy file"
        
        # Update database
        new_url="http://localhost:9000/avatars/$file_path"
        docker compose exec db psql -U user -d finance_db -c "UPDATE users SET avatar_url = '$new_url' WHERE email = '$email';" > /dev/null
        
        echo "✅ Updated: $email"
        echo ""
    fi
done

echo "🎉 Migration complete!"
