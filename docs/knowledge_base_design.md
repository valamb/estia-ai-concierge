# ESTIA — Knowledge Base Design

## Purpose

The `knowledge/` folder is the **source of truth** for all hotel information. It contains structured Markdown documents that describe every service, facility, and policy across all three properties.

These documents are human-readable, easy to edit, and designed for clean ingestion into the ChromaDB vector store.

---

## Folder Structure

```
knowledge/
│
├── properties/              # General property information
│   ├── porto_elounda/
│   │   ├── overview.md      # Property overview, location, contact
│   │   ├── rooms.md         # Room categories, amenities
│   │   ├── facilities.md    # Pools, beach, gym
│   │   └── policies.md      # Check-in/out, cancellation
│   ├── elounda_mare/
│   │   ├── overview.md
│   │   ├── rooms.md
│   │   ├── facilities.md
│   │   └── policies.md
│   └── elounda_peninsula/
│       ├── overview.md
│       ├── rooms.md
│       ├── facilities.md
│       └── policies.md
│
├── restaurants/
│   ├── aura_restaurant.md       # Menu highlights, hours, dress code
│   ├── blue_lagoon.md
│   ├── theodosi.md
│   └── dining_overview.md       # General dining philosophy & hours
│
├── bars/
│   ├── pool_bar.md
│   ├── lobby_bar.md
│   └── sunset_bar.md
│
├── spa/
│   ├── spa_overview.md          # Philosophy, opening hours, booking
│   ├── treatments_menu.md       # Full list of treatments & prices
│   ├── wellness_programs.md     # Packages, retreats
│   └── beauty_salon.md
│
├── sports/
│   ├── golf.md                  # Golf course details, booking
│   ├── tennis.md
│   ├── watersports.md
│   ├── fitness_center.md
│   └── activities_overview.md
│
├── family/
│   ├── kids_club.md             # Ages, activities, schedule
│   ├── babysitting.md
│   └── family_amenities.md
│
├── transportation/
│   ├── airport_transfers.md     # Routes, pricing, booking
│   ├── car_rental.md
│   ├── local_taxis.md
│   └── helicopter.md
│
└── premium/
    ├── vip_services.md          # Butler service, concierge
    ├── yacht_charters.md        # Vessels, itineraries, pricing
    ├── private_events.md        # Weddings, corporate events
    └── exclusive_experiences.md
```

---

## Document Format Standard

Every knowledge document follows this Markdown structure:

```markdown
# [Service / Facility Name]

## Property
[Porto Elounda | Elounda Mare | Elounda Peninsula | All Properties]

## Category
[restaurant | bar | spa | sports | family | transportation | premium]

## Overview
Brief description (2-3 sentences).

## Details
Specific information, hours, prices, policies.

## Booking
How to book or inquire.

## Contact
Phone, email, or in-person location.
```

---

## Why Markdown?

- Human-readable and easy to maintain by hotel staff
- Clean chunking by headings for RAG
- No special software required to edit
- Version-controlled in Git (track changes over time)

---

## Ingestion Process

When documents change:
1. Edit or add `.md` files in `knowledge/`
2. Run: `python -m app.scripts.ingest_knowledge`
3. ChromaDB is updated with the new content
4. No application restart needed
