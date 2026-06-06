# PRD

## Product Name

NetWorkspace

## Product Definition

A platform that helps users onboard job-related websites, collect structured recruitment data, preserve historical snapshots, analyze trends, and build personal AI-assisted tools inside isolated workspaces.

## Product Identity

- Product: `NetWorkspace`
- Crawling engine: `SpiderCore`
- AI assistant: `Todd`
- Core concept: each user receives a stable base system plus an isolated personal workspace that can evolve safely over time

## Core Product Principles

1. Stable core system, isolated personal customization.
2. Minimal user input, strong system workflow.
3. AI assists understanding, generation, repair, and explanation.
4. Critical AI outputs must be previewable, auditable, and reversible.
5. Raw data and structured data must both be preserved.

## Core User Flow

1. User submits a target website link.
2. System identifies page/site type.
3. System optionally gathers supplementary public signals from the web.
4. AI generates a template draft.
5. System runs a small validation sample.
6. User reviews and confirms the result.
7. Template is saved into the user's personal workspace.
8. User creates crawl jobs and explores results through search, dashboards, and AI assistants.

## V1 Scope

- Frontend/backend separation
- User accounts and workspace isolation
- Official template system
- Personal template system
- AI-assisted site onboarding
- Async crawl jobs
- Search, filter, pagination, export
- Analytics dashboards
- Admin review for shared template proposals
- Knowledge base and audit trail

## Non-Goals For V1

- arbitrary user code execution
- fully automatic production template publishing
- direct Agent modification of core production code
- guaranteed one-click support for all websites

## Key Modules

- Workspace
- Template Center
- Intelligent Site Onboarding
- Crawl Task Center
- Data Center
- Analytics Center
- AI Assistant / Agent Layer
- Admin & Review Center
- Knowledge Base & Audit Layer

## Product Theme

NetWorkspace is not just a crawler website. It is a guided workspace for students, early-career job seekers, and people re-entering the market under AI-era change.

The platform should feel:

- approachable
- growth-oriented
- transparent
- customizable without becoming chaotic

Todd, the AI assistant, should help users move from confusion to clarity while keeping evidence and system behavior explicit.

## Success Metrics

- Time to onboard a new site
- First-pass template validation success rate
- Crawl task success rate
- Structured field completeness
- User workspace retention
- Shared template adoption rate
