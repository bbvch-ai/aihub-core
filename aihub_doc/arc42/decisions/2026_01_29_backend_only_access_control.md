# Backend-Only Access Control

## Context

When implementing access control for the hierarchical permission system, two key challenges emerged:

1. **Authorization Location**: Should authorization checks happen in both frontend (hiding UI elements) and backend (
   enforcing access), or exclusively on the backend?

2. **Service Visibility vs Service Access**: A "basic user" who only needs to chat with agents must have
   `aihub.user.service.agent` and `aihub.user.service.thread` permissions to use the chat functionality. However,
   granting these permissions previously made the Agent and Thread service management pages visible in the suite
   navigation, exposing configuration UI not meant for basic users.

The dual-enforcement approach would allow proactive hiding of inaccessible features by checking permissions before
rendering UI or making API calls. However, this creates fundamental concerns around security, maintainability, and
consistency. Additionally, it fails to solve the service visibility problem since the frontend would see the user has
service access and display it in navigation.

## Decision Drivers

- **Security Boundary**: Client-side code can be inspected and bypassed—true enforcement must happen server-side
- **Single Source of Truth**: Duplicating authorization logic across frontend and backend creates drift risk
- **Chat-Only User Experience**: Basic users need service endpoint access for chat without seeing service management UI
- **Separation of Concerns**: Using a service (calling endpoints) should be distinct from managing a service (admin UI)
- **Permission Complexity**: The hierarchical permission system with wildcards is complex enough without replicating it
- **API Contract Clarity**: Backend should be the definitive authority on what a user can access

## Decision

We implement two complementary approaches to separate service access from service visibility:

### 1. Backend-Only Access Control

All access control checks are performed exclusively on the backend using `AccessChecker`. The frontend:

1. Makes API calls without preemptive permission checks
2. Handles HTTP 403 Forbidden responses with graceful error messaging
3. Does NOT use permission-based conditional rendering (`v-if` on assumed permissions)

### 2. Admin-Only Suite Visibility

The `/api/v1/suite` endpoint restricts service visibility to admin-level access:

- Previously: Showed services where `user_service_access != ACCESS_DENIED` (user OR admin)
- Now: Shows services where `user_service_access == ACCESS_ADMIN` (admin only)

This separates **service visibility** (what appears in navigation) from **service access** (what endpoints user can
call):

- Basic users with `aihub.user.service.agent` can call agent endpoints for chat functionality
- But the Agent service management page only appears in navigation for users with `aihub.admin.service.agent`
- Backend still enforces actual access control on all endpoints regardless of suite visibility

**Alternative Considered: Dual Enforcement (Frontend + Backend)**

- Frontend checks permissions via suite configuration to hide inaccessible UI elements
- Backend enforces actual access control
- **Rejected because**: Creates duplication, security false-sense, and maintenance burden. Also fails to separate
  service visibility from service access—users would see all services they can access, defeating the "chat-only" use
  case.

## Consequences

### Positive

- **True Security**: Authorization enforced where it cannot be bypassed
- **Single Authority**: Backend is the definitive source for "can user access X?"
- **Chat-Only Users Enabled**: Basic users can use agents in chat without seeing service management UI
- **Clear Role Separation**: Admin users see management UI, regular users use services without UI clutter
- **Simpler Frontend**: No permission logic duplication in UI layer
- **Easier Permission Changes**: Update authorization rules in one place only

### Negative

- **Brief UI Flicker**: Users may see loading states for resources they cannot access before 403
- **Wasted API Calls**: Frontend will attempt calls that backend will deny
- **Error Handling Requirement**: Frontend must gracefully handle authorization failures everywhere
- **Suite Limited Utility**: Suite endpoint now only useful for admin navigation, not for discovering available services

### Trade-offs

- **Service Discovery**: Regular users cannot use `/api/v1/suite` to discover what services they have access to—they
  must know the endpoints directly or receive 403 errors when attempting access