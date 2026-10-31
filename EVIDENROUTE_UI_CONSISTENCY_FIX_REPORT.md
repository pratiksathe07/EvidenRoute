# EvidenRoute — UI Density, Chat Layout & Consistency Implementation Report

**Author**: Senior UI/UX Engineer & Full-Stack Architect  
**Project**: EvidenRoute Intelligent Context Selection Engine  
**Date**: October 31, 2026  
**Status**: Verified & Build Complete (`npm run build` exited with code 0)

---

## 1. Executive Summary

This engineering effort refactored EvidenRoute's frontend interface to establish layout density, conversational ergonomics, visual consistency, and predictable interactions across the application. 

Using **Resource Ranking** as the baseline specification for page width (`max-width: 1200px`), section headers, border radiuses, and vertical rhythm (`gap: 1.25rem`), we targeted four core user surfaces:

1. **Query Workspace**: Transformed from an analytical dashboard into a streamlined, ChatGPT-like conversational AI interface. We eliminated the redundant inner page header, removed oversized card wrappers, centered the chat thread at a comfortable maximum width (`800px`), anchored a sticky composer at the bottom with full keyboard ergonomics (`Enter` to send, `Shift+Enter` for newline), and restricted suggested question chips strictly to empty conversation states.
2. **Resource Ranking (Reference Specification)**: Maintained strictly as the application standard for container alignment, border treatments, spacing hierarchy, and button design tokens.
3. **Evaluation Page**: Compacted excessive whitespace across the hero quality card, dataset summary, and factor breakdown. The four foundational factors (*Relevance*, *Freshness*, *Correctness*, *Authority*) are presented in a high-density comparative grid with 6px progress indicators and clear typography.
4. **Settings Page**: Aligned with the 1200px container width, normalized form controls to standard 38px heights, and organized Google Gemini API configuration, resource toggles, and service adapters with clear visual hierarchy.
5. **Evidence Explorer**: Elevated search bar prominence with subtle box-shadows and emerald focus states. Diagnosed and permanently resolved the **Inspect Evidence button hover bug** (which previously caused the background to turn white and text to become unreadable) by introducing high-contrast, bulletproof CSS state definitions.

---

## 2. Query Workspace — ChatGPT-Style Interface Refactoring

### 2.1 Problem Analysis
Previously, the Query Workspace contained a redundant page header (`.qw-header`) repeating the page title "Query Workspace" with a subtitle and decorative avatar directly beneath the application-level header. In addition, when empty, the interface rendered a bulky boxed card (`.qw-welcome-card`) with heavy borders and excessive padding, giving it the feel of an administrative dashboard rather than an intuitive conversational assistant.

### 2.2 Implemented Architectural Changes
- **Header Elimination**: Completely removed the internal `<header className="qw-header">` and the duplicate title/subtitle block. The application-level header (`MainLayout` -> `Header`) provides context, leaving the entire workspace canvas dedicated to dialogue.
- **Conversational Width**: Centered the conversation thread in a dedicated container with `max-width: 800px; width: 100%; margin: 0 auto; height: calc(100vh - var(--header-height, 64px) - 3.5rem);`.
- **Empty State & Suggestion Chips**: 
  - When `messages.length === 0`, users see a clean conversational greeting (*"How can EvidenRoute help you verify today?"*) and a compact 2-column grid of 4 suggested question cards with subtle hover elevation (`rgba(0, 184, 113, 0.04)` background and emerald border).
  - When an inquiry is submitted, suggested question chips immediately unmount, yielding full vertical space to the conversation thread.
- **Top Reset Action**: When `messages.length > 0`, a subtle, unobtrusive "New Chat" button (`.qw-reset-btn`) appears at the top right of the thread, allowing users to start a fresh thread with one click without cluttering the view.
- **Message Bubbles & Grounding Association**:
  - User messages: Rendered on the right with brand accent background (`#00B871`), white text, and clean rounded corners (`border-bottom-right-radius: 3px`).
  - Assistant responses: Rendered on the left in white card surfaces with `border: 1px solid var(--border-color)` and subtle box-shadow (`0 1px 2px rgba(15, 23, 42, 0.04)`).
  - Grounding explanations and citations (`.qw-grounding-section`) are attached directly beneath the generated answer, complete with authority percentages and an accordion toggle (`.qw-evidence-toggle-btn`) for viewing retrieved passage text and selection rationale.
- **Sticky Message Composer**:
  - Positioned via `position: sticky; bottom: 0; background: var(--bg-primary); z-index: 10;`.
  - Contained inside a pill-style input card (`border-radius: 20px; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);`).
  - Implemented keyboard handling on `textarea`: `Enter` sends the message; `Shift + Enter` inserts a line break.
  - Composer never overlaps message content; auto-scrolls smoothly to bottom via `messagesEndRef`.

---

## 3. Resource Ranking — Reference Design Specification

The Resource Ranking page was established as the layout and spacing reference:

```css
/* Resource Ranking Layout Standards */
.rr-container {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  padding: 1.5rem;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

/* Header Container */
.rr-header {
  padding: 1.25rem 1.5rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg); /* 12px */
}

/* Action Input Container */
.rr-input-wrap {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 0.5rem 0.85rem;
  transition: border-color 0.2s;
}

/* Primary Action Button */
.rr-analyze-btn {
  background: var(--accent-primary); /* #00B871 */
  color: #ffffff;
  border: none;
  padding: 0.55rem 1.15rem;
  border-radius: var(--radius-md); /* 8px */
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.rr-analyze-btn:hover:not(:disabled) {
  background: var(--accent-hover); /* #009E60 */
}
```

All other pages (`EvaluationPage`, `SettingsPage`, `EvidenceExplorerPage`, `DashboardPage`) were aligned to these exact layout tokens.

---

## 4. Evaluation Page — Whitespace Reduction & High-Density Factors

### 4.1 Whitespace Compaction
- **Page Container**: Set to `max-width: 1200px; margin: 0 auto; padding: 1.5rem; gap: 1.25rem;` matching Resource Ranking.
- **Hero Quality Card**:
  - Re-architected `.eval-hero-card` to use `padding: 1.15rem 1.35rem; gap: 1.25rem;`.
  - Reduced score typography from `2.75rem` to `2.25rem`, preventing vertical inflation while maintaining high visual hierarchy.
  - Embedded the dataset evaluation summary side-by-side with the quality score box, placing verified benchmarks, noise reduction percentage, and precision gains directly alongside the overall score.
- **The Four Evidence Factors**:
  - Arranged in a responsive 4-column or auto-fit grid (`grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 0.85rem;`).
  - Card padding streamlined to `1rem 1.15rem; gap: 0.5rem;`.
  - Meter bar height standardized to a compact `6px` with smooth transitions.
  - Factor score pills styled with subtle emerald badges (`background: rgba(0, 184, 113, 0.1); border: 1px solid rgba(0, 184, 113, 0.2); font-weight: 700; color: #10B981;`).
- **Benchmark Comparison & Test Queries**:
  - Benchmark performance comparison table padded compactly (`0.65rem 0.85rem` headers and `0.75rem 0.85rem` cells).
  - Test query inspection cards structured with a 4-metric score strip (`Relevance`, `Freshness`, `Correctness`, `Authority`) using `background: var(--bg-secondary); padding: 0.4rem 0.6rem; border-radius: 6px;`.
  - Preserved all live backend benchmark metrics without mock data.

---

## 5. Settings Page — Layout Standardization & Control Alignment

### 5.1 Structure & Spacing
- Aligned container to `max-width: 1200px; margin: 0 auto; padding: 1.5rem; gap: 1.25rem;`.
- Streamlined section headers (`.set-section-header`) with subtle metadata labels.
- Standardized section cards (`.set-card`) to `background: var(--bg-card); border: 1px solid var(--border-color); border-radius: var(--radius-md); padding: 1.15rem 1.35rem; gap: 1rem;`.

### 5.2 Control Normalization
- **Standard 38px Height**: Form input wrappers (`.set-input-password-wrap`), text inputs (`.set-input`), and select dropdowns (`.set-select`) now share a unified 38px height, eliminating visual unevenness.
- **Button Tokens**:
  - Primary save button (`.set-btn.primary`): `background-color: var(--accent-primary); color: #ffffff !important; border: 1px solid var(--accent-primary);` with hover state `var(--accent-hover)`.
  - Secondary test button (`.set-btn.secondary`): `background-color: var(--bg-secondary); border: 1px solid var(--border-color); color: var(--text-primary);` with hover background `var(--bg-surface-hover)`.
- **Resource Connection Toggles**:
  - Replaced bulky toggle controls with compact status buttons (`.set-toggle-btn.active` and `.set-toggle-btn.inactive`) providing instant visual feedback.
- **External Integrations**:
  - Formatted into a responsive multi-column grid (`minmax(260px, 1fr)`) with compact adapter tags and status pills.

---

## 6. Evidence Explorer — Search Bar Prominence & Inspect Button Fix

### 6.1 Search Bar Prominence Enhancement
- **Placement**: Positioned immediately below the page header in an aligned inquiry section.
- **Visual Separation**:
  - Added subtle elevation shadow: `box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08), 0 1px 2px rgba(15, 23, 42, 0.04);`.
  - Set border to `var(--border-strong, #CBD5E1)`.
  - Implemented prominent emerald focus ring: `border-color: #00B871; box-shadow: 0 0 0 3px rgba(0, 184, 113, 0.2), 0 1px 3px rgba(15, 23, 42, 0.08);`.
  - Fully accessible across desktop, tablet, and mobile breakpoints.

### 6.2 Inspect Evidence Button Hover Issue — Root Cause & Permanent Solution
- **Root Cause**:
  In `EvidenceExplorerPage.css`, `.ee-inspect-btn:hover:not(:disabled)` had referenced `background: var(--accent-hover);`. In certain execution contexts and browser rendering trees where `--accent-hover` was undefined or reset by global CSS resets (`button { background: none; }` and inherit rules in `index.css`), the browser evaluated the property to transparent or white. Combined with light card backgrounds and global white button styling, the button became pure white against white text, making the button completely invisible.
- **Permanent Solution**:
  Implemented explicit, high-specificity state styling using strict hexadecimal color values and `!important` color locks:

```css
/* Normal State */
.ee-inspect-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background-color: #00B871 !important;
  color: #ffffff !important;
  border: 1px solid #00B871 !important;
  padding: 0.55rem 1.25rem;
  border-radius: var(--radius-md);
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  box-shadow: 0 1px 2px rgba(0, 184, 113, 0.2);
  transition: background-color 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease, transform 0.1s ease;
}

/* Hover State - Strictly Dark Emerald, Never White */
.ee-inspect-btn:hover:not(:disabled) {
  background-color: #009E60 !important;
  border-color: #009E60 !important;
  color: #ffffff !important;
  box-shadow: 0 2px 6px rgba(0, 158, 96, 0.35);
  transform: translateY(-1px);
}

/* Focus Visible State */
.ee-inspect-btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(0, 184, 113, 0.35);
}

/* Active Pressed State */
.ee-inspect-btn:active:not(:disabled) {
  background-color: #008450 !important;
  border-color: #008450 !important;
  color: #ffffff !important;
  transform: translateY(1px);
}

/* Disabled State */
.ee-inspect-btn:disabled {
  background-color: var(--border-subtle, #E2E8F0) !important;
  border-color: var(--border-subtle, #E2E8F0) !important;
  color: var(--text-muted, #94A3B8) !important;
  cursor: not-allowed;
  opacity: 0.65;
  box-shadow: none;
  transform: none;
}
```

In addition, `--accent-hover: #009E60;` was added directly into `:root` in `frontend/src/index.css`.

---

## 7. Design Token & Color Consistency Audit

All pages consistently adhere to the project's central design tokens without introducing third-party UI frameworks or Tailwind CSS:

| Token | Value | Purpose |
| :--- | :--- | :--- |
| `--accent-primary` | `#00B871` | Primary actions, user message bubbles, active highlights |
| `--accent-primary-hover` / `--accent-hover` | `#009E60` | Button hover state across all primary actions |
| `--accent-primary-light` | `#ECFDF5` | Subtle emerald tint on verified badges |
| `--bg-primary` | `#F8FAFC` | Main application workspace canvas |
| `--bg-card` / `--bg-surface` | `#FFFFFF` | Cards, panels, input wraps, and chatbot response bubbles |
| `--bg-secondary` | `#F1F5F9` | Secondary surfaces, chips, and table headers |
| `--border-color` / `--border-subtle` | `#E2E8F0` | Dividers, card borders, and table rows |
| `--border-strong` | `#CBD5E1` | Input container borders |
| `--text-primary` | `#0F172A` | Slate 900 headings and body text (AAA contrast) |
| `--text-secondary` | `#64748B` | Slate 500 metadata and explanations |
| `--text-muted` | `#94A3B8` | Slate 400 helper notes and placeholders |

---

## 8. Verification & Build Results

### 8.1 TypeScript & Vite Production Compilation
The complete frontend was compiled using the production pipeline:

```bash
npm run build --prefix frontend
```

**Result**:
```
> evidenroute-frontend@0.1.0 build
> tsc -b && vite build

vite v6.4.5 building for production...
transforming...
✓ 1665 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   1.14 kB │ gzip:  0.64 kB
dist/assets/index-Z2Kchrb0.css   53.52 kB │ gzip:  8.90 kB
dist/assets/index-ZW07ENGD.js   318.30 kB │ gzip: 98.35 kB
✓ built in 6.68s
```
**Exit Code**: `0` (Zero TypeScript diagnostics, zero CSS bundle warnings).

### 8.2 Hot Module Replacement (HMR) Verification
Live changes were observed across running daemons without errors:
- `QueryWorkspacePage.tsx` and `.css` hot-reloaded
- `EvaluationPage.tsx` and `.css` hot-reloaded
- `SettingsPage.tsx` and `.css` hot-reloaded
- `EvidenceExplorerPage.tsx` and `.css` hot-reloaded
- `DashboardPage.css` and `ResourceRankingPage.css` hot-reloaded

### 8.3 Interaction & Accessibility Verification
- **Query Workspace**: Tested Enter-to-send and Shift+Enter for new line; verified suggested question chips show only when thread is empty.
- **Inspect Evidence Button**: Inspected normal (`#00B871`), hover (`#009E60`), active (`#008450`), and disabled states. The button remains high-contrast with crisp white text.
- **Search Bar**: Prominently visible near top with emerald focus ring and subtle shadow.
- **Layout Alignment**: All 5 pages now render with consistent 1200px max width and 1.25rem spacing.

---

## 9. Summary of Modified Files

1. `frontend/src/index.css`: Added `--accent-hover` alias token and cleaned global variables.
2. `frontend/src/pages/QueryWorkspacePage.tsx`: Removed internal header and duplicate title; refined ChatGPT message thread, suggested questions logic, and keyboard bindings.
3. `frontend/src/pages/QueryWorkspacePage.css`: Centered conversation column (`max-width: 800px`), sticky bottom composer, and minimal clean bubbles.
4. `frontend/src/pages/ResourceRankingPage.css`: Responsive alignment container standard.
5. `frontend/src/pages/EvaluationPage.tsx`: Compacted score summary and streamlined 4-factor layout.
6. `frontend/src/pages/EvaluationPage.css`: Whitespace reduction, 1200px container width, and 6px progress meters.
7. `frontend/src/pages/SettingsPage.tsx`: Normalized section forms, Gemini configuration, and resource toggles.
8. `frontend/src/pages/SettingsPage.css`: Aligned 1200px layout and standard 38px form controls.
9. `frontend/src/pages/EvidenceExplorerPage.tsx`: Enhanced provenance inspection with typed fields and prominent search bar.
10. `frontend/src/pages/EvidenceExplorerPage.css`: Elevated search bar visibility and bulletproof Inspect Evidence button states.
11. `frontend/src/pages/DashboardPage.css`: Aligned container max-width to 1200px.

