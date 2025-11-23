# Tags and Notes System - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                       FastAPI Application                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    API Layer (main.py)                       │   │
│  │  - Tags Router        /api/v1/tags                           │   │
│  │  - Notes Router       /api/v1/notes                          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                    ┌─────────┴──────────┐                            │
│                    │                    │                            │
│  ┌──────────────────────────┐  ┌────────────────────────┐           │
│  │ Tags Endpoints           │  │ Notes Endpoints        │           │
│  │ (tags.py)                │  │ (notes.py)             │           │
│  │ - get_tags()             │  │ - get_lead_notes()     │           │
│  │ - create_tag()           │  │ - create_note()        │           │
│  │ - update_tag()           │  │ - update_note()        │           │
│  │ - delete_tag()           │  │ - delete_note()        │           │
│  │ - get_lead_tags()        │  │ - get_note()           │           │
│  │ - add_tag_to_lead()      │  └────────────────────────┘           │
│  │ - add_tag_by_name()      │                                       │
│  │ - remove_tag_from_lead() │                                       │
│  └──────────────────────────┘                                       │
│                    │                    │                            │
│                    └─────────┬──────────┘                            │
│                              │                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Pydantic Schemas (Validation)                   │   │
│  │                                                               │   │
│  │  Tags:              Notes:                                    │   │
│  │  - TagCreate        - NoteCreate                              │   │
│  │  - TagUpdate        - NoteUpdate                              │   │
│  │  - TagResponse      - NoteResponse                            │   │
│  │  - LeadTagResponse  - NoteListResponse                        │   │
│  │  - AddTagRequest                                              │   │
│  │  - AddTagByNameRequest                                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                    ┌─────────┴──────────┐                            │
│                    │                    │                            │
│  ┌──────────────────────────┐  ┌────────────────────────┐           │
│  │  SQLAlchemy ORM Models   │  │  SQLAlchemy ORM Models │           │
│  │                          │  │                        │           │
│  │  Tag Model (tags.py)     │  │  Note Model (notes.py) │           │
│  │  - id                    │  │  - id                  │           │
│  │  - name (unique)         │  │  - lead_id (FK)        │           │
│  │  - color                 │  │  - content             │           │
│  │  - category              │  │  - author_id           │           │
│  │  - created_at            │  │  - created_at          │           │
│  │  - lead_tags (rel)       │  │  - updated_at          │           │
│  │                          │  │                        │           │
│  │  LeadTag Model           │  └────────────────────────┘           │
│  │  (junction table)        │                                       │
│  │  - lead_id (FK, PK)      │                                       │
│  │  - tag_id (FK, PK)       │                                       │
│  │  - created_at            │                                       │
│  │  - tag (rel)             │                                       │
│  └──────────────────────────┘                                       │
│                    │                    │                            │
│                    └─────────┬──────────┘                            │
│                              │                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │            PostgreSQL Database (async)                       │   │
│  │            SQLAlchemy AsyncSession                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                       │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
          ┌──────────────────┐  ┌─────────────────┐
          │  tags table      │  │  notes table    │
          ├──────────────────┤  ├─────────────────┤
          │ id (PK)          │  │ id (PK)         │
          │ name (UNIQUE)    │  │ lead_id (FK)    │
          │ color            │  │ content         │
          │ category         │  │ author_id       │
          │ created_at       │  │ created_at      │
          └──────────────────┘  │ updated_at      │
                    │           └─────────────────┘
                    │                     │
                    └──────────┬──────────┘
                               │
          ┌────────────────────────────────┐
          │  lead_tags table (junction)    │
          ├────────────────────────────────┤
          │ lead_id (FK, PK)               │
          │ tag_id (FK, PK)                │
          │ created_at                     │
          └────────────────────────────────┘
```

## Data Flow Diagrams

### Creating and Adding a Tag to Lead

```
Client Request
    │
    ├─ POST /api/v1/tags (Create Tag)
    │   │
    │   ├─> TagCreate Schema (validation)
    │   │
    │   ├─> create_tag() endpoint
    │   │   │
    │   │   ├─> Check unique name constraint
    │   │   │
    │   │   ├─> Create Tag model instance
    │   │   │
    │   │   ├─> db.add() and db.commit()
    │   │   │
    │   │   └─> Return TagResponse
    │   │
    │   └─ 201 Created: Tag object
    │
    ├─ POST /api/v1/tags/{lead_id}/tags (Add Tag to Lead)
    │   │
    │   ├─> AddTagRequest Schema (validation)
    │   │
    │   ├─> add_tag_to_lead() endpoint
    │   │   │
    │   │   ├─> Verify lead exists
    │   │   │
    │   │   ├─> Verify tag exists
    │   │   │
    │   │   ├─> Check for duplicate association
    │   │   │
    │   │   ├─> Create LeadTag model instance
    │   │   │
    │   │   ├─> db.add() and db.commit()
    │   │   │
    │   │   └─> Return LeadTagResponse
    │   │
    │   └─ 201 Created: LeadTag object with nested Tag
    │
    └─ Response to Client
```

### Creating and Retrieving Notes

```
Client Request
    │
    ├─ POST /api/v1/notes/{lead_id}/notes (Create Note)
    │   │
    │   ├─> NoteCreate Schema (validation)
    │   │
    │   ├─> create_note() endpoint
    │   │   │
    │   │   ├─> Verify lead exists
    │   │   │
    │   │   ├─> Create Note model instance
    │   │   │
    │   │   ├─> db.add() and db.commit()
    │   │   │
    │   │   └─> Return NoteResponse
    │   │
    │   └─ 201 Created: Note object
    │
    ├─ GET /api/v1/notes/{lead_id}/notes (Get Notes)
    │   │
    │   ├─> get_lead_notes() endpoint
    │   │   │
    │   │   ├─> Verify lead exists
    │   │   │
    │   │   ├─> Count total notes for lead
    │   │   │
    │   │   ├─> Query notes ordered by created_at DESC
    │   │   │
    │   │   ├─> Apply pagination (skip/limit)
    │   │   │
    │   │   └─> Return NoteListResponse
    │   │
    │   └─ 200 OK: Paginated list of notes
    │
    └─ Response to Client
```

## Entity Relationship Diagram

```
┌─────────────────────┐
│      leads          │
├─────────────────────┤
│ id (PK)      ◄──┐   │
│ title            │   │
│ description      │   │
│ email            │   │
│ location_id      │   │
│ created_at       │   │
│ ... (other)      │   │
└─────────────────────┘
        │ (1)
        │
        │ (M)
        ├──────────────────────────┐
        │                          │
    ┌───┴──────────────────┐      │
    │                      │      │
┌───┴───────────────┐ ┌───┴──────────────────┐
│   lead_tags       │ │     notes           │
├───────────────────┤ ├─────────────────────┤
│ lead_id (PK,FK) ──┼─┤                     │
│ tag_id (PK,FK)  ──┘ │ lead_id (FK) ──────┼─┐
│ created_at          │ id (PK)             │ │
└─────────┬───────────┤ content             │ │
          │           │ author_id           │ │
          │ (M)       │ created_at          │ │
          │           │ updated_at          │ │
          │           └─────────────────────┘ │
          │                                   │
          │ (M)                              (1)
    ┌─────┴──────────────┐                  │
    │                    │                  │
┌───┴──────────────────┐ │              Lead │
│      tags            │ │            (1)  │
├──────────────────────┤ │                  │
│ id (PK)          ◄───┴──┐                 │
│ name (UNIQUE)           │              ───┘
│ color                   │
│ category                │
│ created_at              │
└─────────────────────────┘

Legend:
┌──────┐
│      │
│ PK   │ = Primary Key
│ FK   │ = Foreign Key
│      │
└──────┘

Relationships:
- Lead (1) to LeadTag (M): One lead can have many tags
- Tag (1) to LeadTag (M): One tag can be applied to many leads
- Lead (1) to Note (M): One lead can have many notes
```

## Request/Response Flow

### Typical Tag Management Workflow

```
1. Get all available tags
   GET /api/v1/tags?limit=50
   Response: { tags: [...], total: 42, page: 0, page_size: 50 }

2. Create a new tag (if needed)
   POST /api/v1/tags
   Body: { "name": "hot_lead", "color": "#FF6B6B", "category": "priority" }
   Response: 201 Created with tag object

3. Add tag to lead (option A: by ID)
   POST /api/v1/tags/42/tags
   Body: { "tag_id": 5 }
   Response: 201 Created with LeadTag object

4. Get lead's tags
   GET /api/v1/tags/42/tags
   Response: 200 OK with list of LeadTag objects

5. Remove tag from lead
   DELETE /api/v1/tags/42/tags/5
   Response: 200 OK with success message

6. Update tag properties
   PUT /api/v1/tags/5
   Body: { "name": "hot_lead_2", "color": "#FF0000" }
   Response: 200 OK with updated tag

7. Delete tag
   DELETE /api/v1/tags/5
   Response: 200 OK with success message
```

### Typical Notes Workflow

```
1. Create note for lead
   POST /api/v1/notes/42/notes
   Body: { "content": "Customer interested in premium plan", "author_id": "user@example.com" }
   Response: 201 Created with note object

2. Get all notes for lead
   GET /api/v1/notes/42/notes?skip=0&limit=10
   Response: 200 OK with paginated list

3. Get specific note
   GET /api/v1/notes/note/1
   Response: 200 OK with note object

4. Update note
   PUT /api/v1/notes/1
   Body: { "content": "Updated content", "author_id": "manager@example.com" }
   Response: 200 OK with updated note

5. Delete note
   DELETE /api/v1/notes/1
   Response: 200 OK with success message
```

## Database Schema

### Table: tags
```sql
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#808080' NOT NULL,
    category VARCHAR(100),
    created_at TIMESTAMP WITH TIMEZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_tags_category ON tags(category);
```

### Table: lead_tags
```sql
CREATE TABLE lead_tags (
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIMEZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    PRIMARY KEY (lead_id, tag_id)
);
```

### Table: notes
```sql
CREATE TABLE notes (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    author_id VARCHAR(255),
    created_at TIMESTAMP WITH TIMEZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIMEZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX idx_notes_lead_id ON notes(lead_id);
```

## Error Handling Strategy

```
┌─────────────────────────────────────────────────────────┐
│              Request Validation Layer                  │
│  (Pydantic Schemas)                                     │
│  - Type validation                                      │
│  - Field constraints (min_length, pattern, etc.)        │
│  - Custom validators                                    │
│                                                         │
│  Error Response: 422 Unprocessable Entity               │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│            Business Logic Layer                         │
│  (Endpoint Functions)                                   │
│  - Verify resources exist                               │
│  - Check constraints (unique names, duplicates)         │
│  - Validate relationships                               │
│                                                         │
│  Error Response: 404 Not Found, 409 Conflict            │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│           Database Operations Layer                     │
│  (SQLAlchemy)                                           │
│  - Execute queries                                      │
│  - Handle database constraints                          │
│  - Manage transactions                                  │
│                                                         │
│  Error Response: 500 Internal Server Error              │
└─────────────────────────────────────────────────────────┘
```

## Performance Characteristics

### Query Optimization

| Operation | Type | Optimization |
|-----------|------|--------------|
| Get tag by name | SELECT | UNIQUE constraint enables index scan |
| List tags | SELECT | Pagination with LIMIT/OFFSET |
| Get lead's tags | SELECT | Foreign key join, eager load tag |
| Add tag to lead | INSERT | Composite PK prevents duplicates |
| Get lead's notes | SELECT | Index on lead_id, ORDER BY created_at |
| Search tags | SELECT | LIKE pattern with index |

### Indexes

| Table | Column(s) | Type | Purpose |
|-------|-----------|------|---------|
| tags | name | UNIQUE | Enforce uniqueness + fast lookup |
| tags | category | B-tree | Category filtering |
| lead_tags | (lead_id, tag_id) | PRIMARY | Fast composite key lookups |
| notes | lead_id | B-tree | Efficient note retrieval by lead |

## Security Considerations

1. **Input Validation**: All inputs validated by Pydantic schemas
2. **SQL Injection**: Protected by SQLAlchemy ORM parameterized queries
3. **Cascade Deletes**: Automatically clean up related data
4. **Unique Constraints**: Database-level enforcement
5. **Authorization**: Can be added at endpoint level (future enhancement)

## Scalability Notes

### Current Limitations
- No pagination on tag retrieval (full load possible)
- No soft deletes (hard deletes only)
- No caching implemented

### Scaling Improvements
1. Add Redis caching for frequently accessed tags
2. Implement soft deletes with archive tables
3. Partition notes by lead_id for very large datasets
4. Add bulk operations endpoints
5. Implement tag trending/analytics

## Testing Coverage Areas

- [x] Model instantiation
- [x] Schema validation
- [x] Endpoint compilation
- [x] Router registration
- [ ] Database operations
- [ ] Error scenarios
- [ ] Pagination
- [ ] Cascade deletes
- [ ] Concurrent requests
- [ ] Performance under load

---

**System fully designed and implemented - Ready for integration testing**
