# Design Specification: Modern Clean Dashboard
**Date:** 2026-02-16
**Topic:** Frontend Redesign

## 1. Overview
A single-page, density-optimized dashboard for home media services. The aesthetic is "Clean & Modern" with a dark theme. The layout uses a **Bento Grid** approach to organize data logically without requiring navigation.

## 2. Aesthetic Direction
- **Theme:** Dark Mode. Deep blue-greys (`slate-950`) for background, slightly lighter (`slate-900`) for cards.
- **Style:** "Clean Functional".
    - Minimal borders (1px distinct or subtle).
    - Rounded corners (standard `rounded-xl`).
    - High contrast text for readability.
    - **No** excessive glassmorphism or blur effects (keep it crisp).
- **Typography:** Inter (or Geist Sans) - default Next.js font.
    - Headers: Bold, Tracking-tight.
    - Data: Monospace variants for numbers/speeds.

## 3. Layout: The Bento Grid
A responsive grid that fills the screen.
- **Top Row (Status):** Time, Global Bandwidth (Up/Down), Disk Space (if available, otherwise summary).
- **Primary Column (Media):** Plex "Now Playing" (High priority) + Recently Added.
- **Secondary Column (Downloads):** qBittorrent active downloads + detailed transfer stats.
- **Tertiary Column/Row (Management):** Sonarr/Radarr Activity & Overseerr Requests.

## 4. Component Details

### 4.1. Global Header
- **Left:** "Media Dashboard" (Simple text).
- **Right:** Clock & Date.

### 4.2. Plex Card
- **State 1: Nothing Playing**: Shows "Recently Added" in a compact horizontal scroll or grid.
- **State 2: Playing**: Large "Hero" banner at the top showing the active stream, with "Recently Added" pushed below.
- **Artwork**: Uses Series Posters (`grandparentThumb`) for shows, Movie Posters for movies.

### 4.3. qBittorrent Card
- **Header**: Upload/Download speed (always visible, big numbers).
- **Body**: Compact list of active downloads.
    - Progress bars are slim.
    - "Errors" is a status indicator that turns Red. Clicking filters the list or opens the modal (existing functionality).

### 4.4. The "Arrs" (Sonarr/Radarr)
- Combined or split vertically.
- List view of "Activity Queue" (what's being grabbed).
- Small pills for status (`Downloading`, `Importing`).

### 4.5. Overseerr
- Compact list of requests.
- "Pending" count number.

## 5. Technical Implementation
- **Framework:** Next.js + Tailwind CSS.
- **Icons:** Lucide React (clean, consistent strokes).
- **Animation:** Subtle layout transitions (using `framer-motion` if available, or simple CSS transitions) when content changes size (e.g., Plex Now Playing appearing).

## 6. Success Criteria
- User can see "What is playing?", "What is downloading?", and "What is broken?" at a glance.
- No scrollbar on standard desktop (1080p+), or minimal scrolling.
- Zero clicks required for status checks.
