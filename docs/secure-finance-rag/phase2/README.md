# Phase 2: Frontend & Agentic UI

**Status**: ✅ Complete  
**Date**: 2026-01-09

---

## Overview

Phase 2 delivers a beautiful, responsive frontend with an innovative agentic UI that visualizes the AI's thought process. Built with Next.js 16, TypeScript, and TailwindCSS with premium animations using Framer Motion.

## What's Included

### Core Features
- ✅ **Document Upload Interface** - Drag-and-drop with real-time status
- ✅ **Agentic Thought Visualization** - Animated AI state machine
- ✅ **Chat Interface** - Streaming responses with citations
- ✅ **Document Viewer** - PDF rendering with highlighting
- ✅ **Dashboard** - Analytics and navigation

### Technology Stack
- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **State**: @tanstack/react-query + Zustand
- **Icons**: Lucide React
- **PDF**: react-pdf + pdfjs-dist

---

## Quick Start

### Prerequisites
```bash
# Node.js 18+ required
node --version  # v18.0.0 or higher

# Backend must be running
docker compose up -d backend celery-worker
```

### Installation
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Open browser
open http://localhost:3000
```

---

## Pages & Routes

### `/dashboard` - Analytics Overview
**Purpose**: Main landing page after login

**Features**:
- Document count statistics
- Storage usage
- Query statistics  
- Recent documents feed
- Quick action buttons

**Try it**: Navigate to `http://localhost:3000/dashboard`

---

### `/documents` - Document Management
**Purpose**: Upload and manage financial documents

**Features**:
- Drag-and-drop upload zone
- File validation (PDF, DOCX, TXT)
- Status tracking (Pending → Processing → Processed)
- Auto-refresh every 3s for processing docs
- Filter by status
- Delete and reprocess actions

**Try it**:
1. Drag a PDF file to upload zone
2. Watch status change automatically
3. Filter by "Processed" to see completed docs

---

### `/chat` - AI Assistant
**Purpose**: Ask questions about your documents

**Features**:
- Agentic thought visualization
- Streaming responses (optional)
- Clickable citations
- Message history
- Copy to clipboard
- Suggested questions

**Try it**:
1. Upload a document first
2. Navigate to Chat
3. Click a suggested question or type your own
4. Watch the AI states animate:
   - 💤 idle → 🔍 searching → 🧠 analyzing → ✨ generating

---

### `/profile` - User Settings
**Purpose**: Manage account settings

**Features**:
- User information
- Logout functionality

---

## Component Architecture

### Document Upload Components

#### `UploadZone.tsx`
**Location**: `frontend/src/components/documents/UploadZone.tsx`

Drag-and-drop file upload with validation.

**Features**:
- Visual feedback on drag (scale + color)
- File type validation
- Size limit (50MB)
- Error display
- Upload progress

**Usage**:
```tsx
import UploadZone from '@/components/documents/UploadZone';

<UploadZone />
```

---

#### `DocumentCard.tsx`
**Location**: `frontend/src/components/documents/DocumentCard.tsx`

Premium card for displaying document info.

**Features**:
- Status badges with color coding
- File metadata (size, date)
- Action buttons (delete, reprocess)
- Gradient icon
- Hover effects

**Props**:
```typescript
interface DocumentCardProps {
  document: Document;
}
```

---

#### `DocumentList.tsx`
**Location**: `frontend/src/components/documents/DocumentList.tsx`

Grid layout with filtering.

**Features**:
- Filter tabs (All, Processed, etc.)
- Responsive grid (1/2/3 columns)
- Empty state
- Auto-refresh for processing docs
- Document count

---

### Chat Components

#### `AgenticThought.tsx` ⭐
**Location**: `frontend/src/components/chat/AgenticThought.tsx`

Animated visualization of AI thinking process.

**States**:
```typescript
type AgentState = 
  | 'idle'       // 💤 Waiting
  | 'searching'  // 🔍 Searching documents
  | 'analyzing'  // 🧠 Analyzing context
  | 'generating' // ✨ Crafting response
  | 'complete'   // ✅ Done
```

**Animations**:
- Entrance: Fade + scale
- Icon: Pulsing scale
- Background: Shimmer gradient
- Progress bar: 0% → 100%
- Dots: Staggered opacity

**Usage**:
```tsx
import AgenticThought from '@/components/chat/AgenticThought';

<AgenticThought 
  state="analyzing" 
  message="Analyzing context..."
/>
```

---

#### `MessageBubble.tsx`
**Location**: `frontend/src/components/chat/MessageBubble.tsx`

Chat message with citations.

**Features**:
- User/Assistant styling
- Clickable citation badges
- Copy to clipboard
- Relative timestamps
- Markdown support

**Props**:
```typescript
interface MessageBubbleProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  citations?: number[];
  onCitationClick?: (num: number) => void;
}
```

---

#### `ChatInput.tsx`
**Location**: `frontend/src/components/chat/ChatInput.tsx`

Auto-resizing input field.

**Features**:
- Auto-resize textarea
- Send button
- Character counter
- Keyboard shortcuts (Enter/Shift+Enter)
- Loading states

---

#### `CitationPanel.tsx`
**Location**: `frontend/src/components/chat/CitationPanel.tsx`

Sliding sidebar showing sources.

**Features**:
- Slides from right
- Source cards with:
  - Source number badge
  - Filename
  - Page number
  - Similarity score bar
- Click to navigate
- Staggered animations

---

### Document Viewer

#### `DocumentViewer.tsx`
**Location**: `frontend/src/components/viewer/DocumentViewer.tsx`

PDF viewer with controls.

**Features**:
- PDF rendering (react-pdf)
- Page navigation (prev/next)
- Zoom in/out
- Citation highlighting (yellow ring)
- Current page indicator

**Props**:
```typescript
interface DocumentViewerProps {
  fileUrl: string;
  fileName: string;
  highlightedPages?: number[];
  onPageChange?: (page: number) => void;
}
```

---

### Navigation

#### `Sidebar.tsx`
**Location**: `frontend/src/components/navigation/Sidebar.tsx`

Main navigation sidebar.

**Features**:
- Dashboard, Documents, Chat, Profile links
- Active state highlighting (gradient)
- Mobile menu (hamburger)
- Logout button
- Logo

**Responsive**:
- Desktop: Fixed sidebar
- Mobile: Slide-out menu with backdrop

---

#### `ProtectedLayout.tsx`
**Location**: `frontend/src/components/layouts/ProtectedLayout.tsx`

Wrapper for authenticated pages.

**Usage**:
```tsx
import ProtectedLayout from '@/components/layouts/ProtectedLayout';

export default function MyPage() {
  return (
    <ProtectedLayout>
      <YourContent />
    </ProtectedLayout>
  );
}
```

---

## State Management

### React Query Hooks

#### `useDocuments(params?)`
**Location**: `frontend/src/hooks/useDocuments.ts`

Fetch and manage documents.

**Features**:
- Auto-refresh every 3s when processing
- Optimistic updates
- Cache invalidation

**Returns**:
```typescript
{
  data: { documents: Document[], total: number },
  isLoading: boolean,
  error: Error | null
}
```

---

#### `useUploadDocument()`
Upload mutation with toast notifications.

**Returns**:
```typescript
{
  mutate: (file: File) => void,
  isPending: boolean
}
```

---

#### `useChat()`
**Location**: `frontend/src/hooks/useChat.ts`

Manage chat state and agent visualization.

**Features**:
- Agent state machine
- Message history
- Citation tracking
- Streaming support

**Returns**:
```typescript
{
  messages: ChatMessage[],
  agentState: AgentState,
  isLoading: boolean,
  currentCitations: CitationInfo[],
  sendMessage: (content: string, stream?: boolean) => void,
  clearMessages: () => void
}
```

---

## API Integration

### Documents API
**File**: `frontend/src/lib/api/documents.ts`

```typescript
documentsApi.upload(file: File)
documentsApi.list(params?)
documentsApi.get(id: string)
documentsApi.delete(id: string)
documentsApi.reprocess(id: string)
```

### Chat API
**File**: `frontend/src/lib/api/chat.ts`

```typescript
chatApi.query(request: QueryRequest)
chatApi.queryStream(request: QueryRequest) // AsyncGenerator
chatApi.history(params?)
chatApi.feedback(messageId, rating)
```

---

## Design System

### Colors

**Gradients**:
```css
primary: from-blue-500 to-purple-600
success: from-green-500 to-emerald-600
warning: from-yellow-500 to-orange-600
error: from-red-500 to-pink-600
```

**Status Colors**:
- Pending: Yellow (`yellow-500`)
- Processing: Blue (`blue-500`)
- Processed: Green (`green-500`)
- Failed: Red (`red-500`)

### Dark Mode
All components support dark mode with `dark:` variants.

**Examples**:
```css
bg-white dark:bg-gray-800
text-gray-900 dark:text-white
border-gray-200 dark:border-gray-700
```

### Animations

**Durations**:
- UI transitions: 200-300ms
- State changes: 1-3s
- Loading: Infinite

**Easings**:
- Standard: `ease-in-out`
- Spring: Custom cubic-bezier
- Linear: For infinite animations

---

## Testing Checklist

### Manual Tests

**Document Upload**:
- [ ] Drag file shows visual feedback
- [ ] Invalid files show error
- [ ] Upload shows progress
- [ ] Status updates automatically
- [ ] Filters work correctly

**Chat Interface**:
- [ ] Agent states transition smoothly
- [ ] Messages appear correctly
- [ ] Citations are clickable
- [ ] Copy works
- [ ] Streaming displays correctly

**Responsiveness**:
- [ ] Mobile menu opens/closes
- [ ] Grid layouts adapt
- [ ] No horizontal scroll

**Dark Mode**:
- [ ] All pages render correctly
- [ ] Text is readable
- [ ] Colors look good

---

## Troubleshooting

### PDF Not Loading
**Issue**: PDF viewer shows error

**Solution**:
1. Check PDF.js worker is loaded
2. Verify file URL is accessible
3. Check browser console for errors

### Auto-refresh Not Working
**Issue**: Document status doesn't update

**Solution**:
1. Check React Query devtools
2. Verify backend is running
3. Check network tab for polling

### Animations Laggy
**Issue**: Framer Motion animations stutter

**Solution**:
1. Reduce motion in browser settings
2. Check for excessive re-renders
3. Use React DevTools profiler

---

## Next Steps

### Phase 3 Ideas
- Advanced RBAC (roles & permissions)
- Multi-tenancy
- Export functionality
- Advanced search
- Batch operations

### Phase 4 Ideas
- CI/CD pipelines
- Production deployment
- Monitoring & logging
- Backup & recovery

---

## Resources

**Documentation**:
- [Next.js Docs](https://nextjs.org/docs)
- [TanStack Query](https://tanstack.com/query/latest)
- [Framer Motion](https://www.framer.com/motion/)
- [react-pdf](https://github.com/wojtekmaj/react-pdf)

**Code**:
- Frontend: `/home/ubuntu/Mochi/frontend/src/`
- Components: `/home/ubuntu/Mochi/frontend/src/components/`
- Hooks: `/home/ubuntu/Mochi/frontend/src/hooks/`

---

## Support

For issues or questions:
1. Check this README
2. Review component code
3. Check browser console
4. Review React Query devtools
