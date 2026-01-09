# Phase 2: Component Guide

Quick reference for all Phase 2 React components.

---

## Document Components

### UploadZone
**Path**: `components/documents/UploadZone.tsx`  
**Purpose**: Drag-and-drop file upload

```tsx  
<UploadZone />
```

**Features**: File validation, progress indicator, error handling

---

### DocumentCard
**Path**: `components/documents/DocumentCard.tsx`  
**Purpose**: Display document with status

```tsx
<DocumentCard document={doc} />
```

**Props**: `{ document: Document }`

---

### DocumentList
**Path**: `components/documents/DocumentList.tsx`  
**Purpose**: Grid of documents with filtering

```tsx
<DocumentList />
```

**Features**: Auto-refresh, filters, empty state

---

## Chat Components

### AgenticThought
**Path**: `components/chat/AgenticThought.tsx`  
**Purpose**: Animated AI state visualization

```tsx
<AgenticThought 
  state="analyzing"
  message="Custom message" 
/>
```

**States**: idle | searching | analyzing | generating | complete

---

### MessageBubble
**Path**: `components/chat/MessageBubble.tsx`  
**Purpose**: Chat message with citations

```tsx
<MessageBubble
  role="assistant"
  content="Response..."
  citations={[1, 2]}
  onCitationClick={(num) => handleClick(num)}
/>
```

---

### ChatInput
**Path**: `components/chat/ChatInput.tsx`  
**Purpose**: Message input field

```tsx
<ChatInput
  onSend={(msg) => send(msg)}
  disabled={loading}
/>
```

---

### CitationPanel
**Path**: `components/chat/CitationPanel.tsx`  
**Purpose**: Sources sidebar

```tsx
<CitationPanel
  citations={citations}
  isOpen={open}
  onClose={() => setOpen(false)}
/>
```

---

## Viewer Components

### DocumentViewer
**Path**: `components/viewer/DocumentViewer.tsx`  
**Purpose**: PDF viewer with controls

```tsx
<DocumentViewer
  fileUrl="/path/to/file.pdf"
  fileName="document.pdf"
  highlightedPages={[1, 3]}
  onPageChange={(page) => console.log(page)}
/>
```

---

## Navigation Components

### Sidebar
**Path**: `components/navigation/Sidebar.tsx`  
**Purpose**: Main app navigation

```tsx
<Sidebar />
```

**Features**: Responsive, active states, logout

---

### ProtectedLayout
**Path**: `components/layouts/ProtectedLayout.tsx`  
**Purpose**: Layout wrapper with sidebar

```tsx
<ProtectedLayout>
  <YourContent />
</ProtectedLayout>
```

---

## Hooks

### useDocuments
```tsx
const { data, isLoading } = useDocuments({ status: 'PROCESSED' });
```

### useUploadDocument
```tsx
const { mutate } = useUploadDocument();
mutate(file);
```

### useChat
```tsx
const { messages, agentState, sendMessage } = useChat();
sendMessage("What's the revenue?");
```

---

## Styling Patterns

### Gradient Button
```tsx
<button className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-4 py-2 rounded-lg">
  Click Me
</button>
```

### Status Badge
```tsx
<span className="px-3 py-1 rounded-full bg-green-100 text-green-700">
  Processed
</span>
```

### Dark Mode Card
```tsx
<div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
  Content
</div>
```
