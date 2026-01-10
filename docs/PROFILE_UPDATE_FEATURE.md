# Profile Update Feature

## Overview
Added functionality to allow users to update their display name and upload/change their avatar picture.

## Changes Made

### Backend Changes

#### 1. Database Model (`backend/app/models.py`)
- Added `avatar_url: Optional[str]` field to the `User` model
- This field stores the S3 URL of the user's avatar image

#### 2. API Endpoints (`backend/app/routers/users.py`)
Added two new endpoints:

**PATCH /users/me**
- Updates the user's display name (full_name)
- Request body: `{ "full_name": "John Doe" }`
- Returns: Updated User object

**POST /users/me/avatar**
- Uploads and updates the user's avatar image
- Request: multipart/form-data with image file
- Validates:
  - File type (must be an image)
  - File size (max 5MB)
- Uploads to S3 bucket in `avatars/{user_id}/` directory
- Sets ACL to 'public-read' for direct access
- Returns: Updated User object with new avatar_url

#### 3. Migration Script (`backend/add_avatar_column.py`)
- Script to add the `avatar_url` column to existing databases
- Run with: `python add_avatar_column.py`
- Safe to run multiple times (checks if column exists first)

### Frontend Changes

#### Profile Page (`frontend/src/app/profile/page.tsx`)
Complete redesign with modern UI featuring:

**Features:**
- Avatar display with placeholder if no avatar set
- Click camera icon to upload new avatar
- Real-time avatar preview
- Loading states during upload
- Display name editing with live save
- Email display (read-only)
- Account information (role, join date)
- Responsive design (mobile-friendly)
- Beautiful gradient styling with animations
- Toast notifications for success/error states

**UI Elements:**
- Large circular avatar with gradient background
- Camera button overlay for quick uploads
- File upload instructions
- Profile information form
- Account details sidebar
- Profile tips section
- Smooth animations and transitions

## Usage

### For Users:
1. Navigate to the Profile page
2. Click the camera icon on the avatar to upload a new image
3. Edit your display name in the form
4. Click "Save Changes" to update your name

### For Developers:

#### Running the Migration:
```bash
cd backend
python add_avatar_column.py
```

#### Environment Variables Required:
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=mochi-documents
```

## API Examples

### Update Display Name:
```bash
curl -X PATCH http://localhost:8000/users/me \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "John Doe"}'
```

### Upload Avatar:
```bash
curl -X POST http://localhost:8000/users/me/avatar \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/image.jpg"
```

### Get Current User:
```bash
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## File Structure
```
backend/
├── app/
│   ├── models.py (Updated: added avatar_url field)
│   └── routers/
│       └── users.py (Updated: added PATCH /me and POST /me/avatar)
└── add_avatar_column.py (New: migration script)

frontend/
└── src/
    └── app/
        └── profile/
            └── page.tsx (Redesigned: new UI with avatar upload)
```

## Security Considerations
- File type validation (images only)
- File size limit (5MB max)
- S3 bucket with proper permissions
- User authentication required for all endpoints
- Files stored in user-specific directories

## Future Enhancements
- Image cropping/resizing before upload
- Support for drag-and-drop upload
- Remove avatar functionality
- Avatar compression for optimization
- Multiple avatar sizes (thumbnail, full)
