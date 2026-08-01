# JAPES UI Implementation Plan

**Status:** Initial structure created
**Date:** 2024-11-30

## ✅ Completed

### Project Structure
- ✅ Created `japes/ui/` directory within JAPES monorepo
- ✅ Set up Vite + React + TypeScript configuration
- ✅ Configured Module Federation for builder-studio integration
- ✅ Created directory structure for components, pages, services
- ✅ Defined TypeScript type definitions
- ✅ Created comprehensive README

### Configuration Files
- ✅ `package.json` - Dependencies and scripts
- ✅ `vite.config.ts` - Build config with Module Federation
- ✅ `tsconfig.json` - TypeScript config with path aliases
- ✅ `index.html` - HTML entry point
- ✅ `.env.example` - Environment variables template
- ✅ `.gitignore` - Git ignore rules

### Type Definitions
- ✅ `Extension` - Extension registry model
- ✅ `ExtensionConfig` - Configuration schema
- ✅ `ExtensionMetrics` - Usage metrics
- ✅ `QueueStats` - Queue monitoring
- ✅ `QueueMessage` - Message inspection
- ✅ `JapesContext` - Federation context

## 🚀 Next Steps

### Phase 1: Core Infrastructure (Week 1)

#### Day 1-2: Base Components & Services
```
Priority: High
Dependencies: None
```

**Tasks:**
1. Create `src/services/apiClient.ts`
   - Axios instance with interceptors
   - SecurityContext integration
   - Error handling

2. Create `src/context/SecurityContext.ts`
   - Module-level JWT storage
   - Token getters for standalone/federated modes

3. Create `src/context/JapesContext.tsx`
   - React context for app state
   - Kernel URL configuration

4. Create `src/core/AppProviders.tsx`
   - Redux store provider
   - Theme provider
   - Router provider
   - Notification provider (notistack)

5. Create `src/core/AppCore.tsx`
   - Main app logic
   - Layout switching (standalone/federated)

#### Day 3-4: Layouts & Navigation
```
Priority: High
Dependencies: Core infrastructure
```

**Tasks:**
1. Create `src/layouts/StandaloneLayout.tsx`
   - Full navigation sidebar
   - Top bar
   - Main content area

2. Create `src/layouts/FederatedLayout.tsx`
   - Minimal wrapper
   - No navigation (provided by builder-studio)

3. Create `src/App.tsx`
   - Standalone mode entry
   - Router configuration

4. Create `src/FederatedApp.tsx`
   - Federation mode entry
   - Context initialization

5. Create `src/main.tsx`
   - Vite entry point
   - Root rendering

#### Day 5: Redux Store Setup
```
Priority: High
Dependencies: Core infrastructure
```

**Tasks:**
1. Create `src/store/index.ts`
   - Configure Redux store
   - Redux Persist setup

2. Create `src/store/slices/extensionSlice.ts`
   - Extension registry state
   - Async thunks for API calls

3. Create `src/store/slices/queueSlice.ts`
   - Queue monitoring state

4. Create `src/store/slices/messageSlice.ts`
   - Message inspection state

5. Create `src/store/slices/uiSlice.ts`
   - UI state (notifications, loading)

### Phase 2: Extension Registry (Week 2)

#### Day 1-2: Extension Services
```
Priority: High
Dependencies: Phase 1 complete
```

**Tasks:**
1. Create `src/services/extensionService.ts`
   ```typescript
   - fetchExtensions()
   - fetchExtensionById(id)
   - registerExtension(data)
   - updateExtension(id, data)
   - fetchExtensionHealth(id)
   - fetchExtensionMetrics(id)
   ```

2. Create mock data for development
3. Test API integration

#### Day 3-5: Extension UI Components
```
Priority: High
Dependencies: Extension services
```

**Tasks:**
1. Create `src/components/ExtensionCard.tsx`
   - Display extension info
   - Health indicator
   - Metrics summary
   - Actions (view, configure, test)

2. Create `src/components/HealthIndicator.tsx`
   - Color-coded status badges
   - Tooltip with details

3. Create `src/pages/ExtensionRegistry.tsx`
   - Extension listing with grid layout
   - Filter by status
   - Search functionality
   - Register extension button

4. Create `src/pages/ExtensionDetail.tsx`
   - Full extension details
   - Configuration editor
   - Metrics dashboard
   - Schema viewer (input/output)

### Phase 3: Extension Picker for BPMN (Week 3)

#### Day 1-2: Extension Picker Component
```
Priority: High (Required for builder-studio integration)
Dependencies: Extension registry
```

**Tasks:**
1. Create `src/components/ExtensionPicker.tsx`
   - Dialog component
   - Extension list with search
   - Health status indicators
   - Select handler
   - Export via Module Federation

2. Create `src/components/index.ts`
   - Export all components for federation

#### Day 3-4: Builder Studio Integration
```
Priority: High
Dependencies: Extension picker complete
```

**Tasks:**
1. Update `builder-studio-ui/vite.config.ts`
   - Add japesApp remote

2. Create `builder-studio-ui/src/process/dialogs/JapesExtensionDialog.jsx`
   - Import ExtensionPicker from japesApp
   - Auto-configure HTTP Service Task
   - Set headers, URL, body

3. Update `builder-studio-ui/src/process/config/activities.json`
   - Add japesExtension property to ServiceTask

#### Day 5: Testing & Documentation
```
Priority: Medium
```

**Tasks:**
1. Test extension picker in BPMN designer
2. Test auto-configuration logic
3. Update documentation
4. Create usage examples

### Phase 4: Queue Monitoring (Week 4)

#### Day 1-2: Queue Services
```
Priority: Medium
Dependencies: Phase 1 complete
```

**Tasks:**
1. Create `src/services/queueService.ts`
   ```typescript
   - fetchQueueStats()
   - fetchRecentMessages()
   - subscribeToQueue() // WebSocket
   ```

2. Implement WebSocket connection for real-time updates

#### Day 3-5: Queue UI Components
```
Priority: Medium
Dependencies: Queue services
```

**Tasks:**
1. Create `src/components/QueueStats.tsx`
   - Queue statistics cards
   - Live updating metrics
   - Visual indicators

2. Create `src/pages/QueueMonitor.tsx`
   - Real-time queue dashboard
   - japes-invocation stats
   - japes-response stats
   - Message feed

### Phase 5: Message Inspector (Week 5)

#### Day 1-2: Message Services
```
Priority: Medium
Dependencies: Phase 1 complete
```

**Tasks:**
1. Create `src/services/messageService.ts`
   ```typescript
   - fetchMessages(filters)
   - fetchMessageById(id)
   - searchMessages(query)
   ```

#### Day 3-5: Message UI Components
```
Priority: Medium
Dependencies: Message services
```

**Tasks:**
1. Create `src/components/MessageViewer.tsx`
   - JSON payload viewer
   - Syntax highlighting
   - Copy to clipboard
   - Expandable sections

2. Create `src/pages/MessageInspector.tsx`
   - Message table with filters
   - Search by correlation key
   - Filter by extension, status, date
   - Detail drawer for selected message

### Phase 6: Extension Testing (Week 6)

#### Day 1-3: Testing Interface
```
Priority: Low
Dependencies: Extension registry, Message inspector
```

**Tasks:**
1. Create `src/pages/ExtensionTester.tsx`
   - Select extension
   - Input editor (JSON)
   - Execute button
   - Response viewer
   - Save test cases

2. Implement test execution
3. Add result history

## 📊 Timeline Summary

| Phase | Duration | Priority | Dependencies |
|-------|----------|----------|--------------|
| Phase 1: Core Infrastructure | Week 1 | High | None |
| Phase 2: Extension Registry | Week 2 | High | Phase 1 |
| Phase 3: BPMN Integration | Week 3 | High | Phase 2 |
| Phase 4: Queue Monitoring | Week 4 | Medium | Phase 1 |
| Phase 5: Message Inspector | Week 5 | Medium | Phase 1 |
| Phase 6: Extension Testing | Week 6 | Low | Phases 2, 5 |

**Total: 6 weeks for complete implementation**

**Minimum Viable Product (MVP): 3 weeks**
- Week 1: Core Infrastructure
- Week 2: Extension Registry
- Week 3: BPMN Integration

## 🎯 Success Criteria

### Phase 1 (Core) Complete When:
- ✅ App runs in standalone mode at localhost:5175
- ✅ Redux store configured
- ✅ API client connects to Kernel
- ✅ Layouts render correctly

### Phase 2 (Registry) Complete When:
- ✅ Can view list of extensions
- ✅ Can view extension details
- ✅ Can register new extension
- ✅ Health status displays correctly

### Phase 3 (BPMN) Complete When:
- ✅ Extension picker works in builder-studio
- ✅ HTTP Service Task auto-configures
- ✅ Workflow can invoke JAPES extension
- ✅ End-to-end flow tested

### Phase 4-6 Complete When:
- ✅ Queue monitoring shows real-time stats
- ✅ Message inspector allows debugging
- ✅ Extension tester allows manual testing

## 🔧 Technical Notes

### Module Federation
- App name: `japesApp`
- Port: 5175
- Exposes: FederatedApp, ExtensionPicker, components
- Consumed by: builder-studio-ui

### API Dependencies
Kernel must implement:
- `/api/japes/extensions` - Extension registry
- `/api/japes/queues` - Queue monitoring
- `/api/japes/messages` - Message inspection
- `/ws` - WebSocket for real-time updates

### State Management
- Redux Toolkit for global state
- Redux Persist for localStorage
- React Query (optional) for API caching

### Security
- JWT tokens via SecurityContext
- Module-level state for federation
- localStorage fallback for standalone

## 📝 Notes

- Start with Phase 1-3 for MVP
- Phase 4-6 are enhancements
- Can deploy after Phase 3
- Focus on Extension Picker first (high value)
