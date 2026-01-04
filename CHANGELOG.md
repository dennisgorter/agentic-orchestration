# Changelog

All notable changes to Agent Orchestrator will be documented in this file.

## [2.0.0] - In Progress

### Added
- Two-agent architecture (Intent Agent + Pollution Agent)
- API versioning (/v1/chat and /v2/chat endpoints)
- Stateless service design (client-side state management)
- AgentMessage protocol with trace_id and correlation_id
- BaseAgent interface for domain agents
- Intent routing system (multi-domain ready)
- Comprehensive Phase 1 refactor plan

### Changed
- Folder structure refactored for multi-agent pattern
- API endpoints now versioned for backward compatibility
- Session management removed in favor of stateless design
- Frontend updated to manage conversation history

### Technical Debt Resolved
- Prepared for horizontal scaling (stateless design)
- Clean separation between routing and domain logic
- Multi-domain expansion now straightforward

---

## [1.0.0] - 2026-01-04

### Summary
Production-ready single-domain agent for car pollution zone eligibility checks. Full-featured chat interface with LangGraph workflow orchestration.

### Features
- **LangGraph Workflow**: 6-node state machine (extract_intent → resolve_car → resolve_zone → fetch_policy → decide → explain)
- **Multi-Intent Support**: Single car queries, fleet queries, policy-only questions
- **Smart Disambiguation**: Automatic clarifying questions for ambiguous inputs
- **7-Language Support**: Auto-detection and localized responses (EN, ES, FR, NL, DE, IT, PT)
- **React Chat UI**: Modern interface with example queries and car context
- **Request Tracing**: Unique trace_id for every request with structured logging
- **Deterministic Rules**: Business logic uses rule engine, not LLM
- **Car Context Preservation**: Maintains car reference across conversation turns

### Technical Stack
- **Backend**: FastAPI 0.104+ with OpenAI GPT-4o-mini integration
- **Frontend**: React 18 + Vite with CSS modules
- **State Management**: In-memory session store with LangGraph AgentState
- **Logging**: Structured JSON logs with trace correlation
- **Testing**: pytest with comprehensive unit/integration tests

### API Endpoints
- `POST /chat` - Main chat endpoint with session management
- `POST /chat/answer` - Answer endpoint for disambiguation
- `GET /health` - Health check with version info

### Architecture Highlights
- Single-agent monolithic design (⭐⭐⭐⭐ - optimal for single domain)
- Mock services for cars, zones, policies (ready for real API integration)
- Retry/repair logic for LLM calls (handles JSON parsing errors)
- CORS enabled for local development

### Documentation
- `README.md` - User-facing overview
- `QUICKSTART.md` - 5-minute setup guide
- `IMPLEMENTATION.md` - Technical implementation details
- `TRACEABILITY.md` - Request tracing and debugging guide
- `ARCHITECTURE_ASSESSMENT.md` - Comprehensive architecture review
- `PHASE1_REFACTOR_PLAN.md` - Two-agent evolution plan
- `MIGRATION_CHECKLIST.md` - Week-by-week migration tasks

### Known Limitations
- Mock data only (no real car/policy APIs)
- In-memory session storage (ephemeral)
- Single domain (pollution zones only)
- No authentication/authorization
- No rate limiting
- No persistent storage

### Bug Fixes
- Fixed VIN context preservation across conversation turns
- Fixed LangGraph recursion limit errors
- Fixed language detection for mixed-language inputs
- Fixed duplicate conversation history entries

---

## Format

This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Version Format**: MAJOR.MINOR.PATCH
- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality additions
- **PATCH**: Backward-compatible bug fixes
