# Tags and Notes API Quick Reference

## Base URL
```
http://localhost:8000/api/v1
```

## Tags API

### List Tags
```
GET /tags
Query Parameters:
  - skip: int (default: 0)
  - limit: int (default: 100, max: 1000)
  - category: string (optional filter)
  - search: string (optional, partial match on name)

Response:
{
  "tags": [
    {
      "id": 1,
      "name": "hot_lead",
      "color": "#FF6B6B",
      "category": "priority",
      "created_at": "2024-11-05T12:00:00+00:00"
    }
  ],
  "total": 42,
  "page": 0,
  "page_size": 100
}
```

### Get Single Tag
```
GET /tags/{tag_id}

Response:
{
  "id": 1,
  "name": "hot_lead",
  "color": "#FF6B6B",
  "category": "priority",
  "created_at": "2024-11-05T12:00:00+00:00"
}
```

### Create Tag
```
POST /tags
Content-Type: application/json

Request:
{
  "name": "hot_lead",
  "color": "#FF6B6B",
  "category": "priority"
}

Response: 201 Created
{
  "id": 1,
  "name": "hot_lead",
  "color": "#FF6B6B",
  "category": "priority",
  "created_at": "2024-11-05T12:00:00+00:00"
}

Errors:
  - 409 Conflict: Tag name already exists
  - 422 Unprocessable Entity: Invalid color format (must be #RGB or #RRGGBB)
```

### Update Tag
```
PUT /tags/{tag_id}
Content-Type: application/json

Request (all fields optional):
{
  "name": "very_hot_lead",
  "color": "#FF0000",
  "category": "priority"
}

Response: 200 OK
{
  "id": 1,
  "name": "very_hot_lead",
  "color": "#FF0000",
  "category": "priority",
  "created_at": "2024-11-05T12:00:00+00:00"
}

Errors:
  - 404 Not Found: Tag doesn't exist
  - 409 Conflict: New name already taken by another tag
```

### Delete Tag
```
DELETE /tags/{tag_id}

Response: 200 OK
{
  "message": "Tag deleted successfully"
}

Note: Removes all lead-tag associations automatically

Errors:
  - 404 Not Found: Tag doesn't exist
```

## Lead Tag Association API

### Get Lead's Tags
```
GET /tags/{lead_id}/tags

Response: 200 OK
[
  {
    "lead_id": 42,
    "tag_id": 1,
    "tag": {
      "id": 1,
      "name": "hot_lead",
      "color": "#FF6B6B",
      "category": "priority",
      "created_at": "2024-11-05T12:00:00+00:00"
    },
    "created_at": "2024-11-05T12:15:00+00:00"
  }
]

Errors:
  - 404 Not Found: Lead doesn't exist
```

### Add Tag to Lead (by Tag ID)
```
POST /tags/{lead_id}/tags
Content-Type: application/json

Request:
{
  "tag_id": 1
}

Response: 201 Created
{
  "lead_id": 42,
  "tag_id": 1,
  "tag": {
    "id": 1,
    "name": "hot_lead",
    "color": "#FF6B6B",
    "category": "priority",
    "created_at": "2024-11-05T12:00:00+00:00"
  },
  "created_at": "2024-11-05T12:15:00+00:00"
}

Errors:
  - 404 Not Found: Lead or tag doesn't exist
  - 409 Conflict: Lead already has this tag
```

### Add Tag to Lead (by Name - Auto-Create)
```
POST /tags/{lead_id}/tags/by-name
Content-Type: application/json

Request:
{
  "name": "verified",
  "color": "#4CAF50",
  "category": "status"
}

Response: 201 Created
{
  "lead_id": 42,
  "tag_id": 2,
  "tag": {
    "id": 2,
    "name": "verified",
    "color": "#4CAF50",
    "category": "status",
    "created_at": "2024-11-05T12:00:00+00:00"
  },
  "created_at": "2024-11-05T12:15:00+00:00"
}

Note: Creates tag if it doesn't exist

Errors:
  - 404 Not Found: Lead doesn't exist
  - 409 Conflict: Lead already has this tag
```

### Remove Tag from Lead
```
DELETE /tags/{lead_id}/tags/{tag_id}

Response: 200 OK
{
  "message": "Tag removed from lead successfully"
}

Errors:
  - 404 Not Found: Association doesn't exist
```

## Notes API

### Get Lead's Notes
```
GET /notes/{lead_id}/notes
Query Parameters:
  - skip: int (default: 0)
  - limit: int (default: 100, max: 1000)

Response: 200 OK
{
  "notes": [
    {
      "id": 1,
      "lead_id": 42,
      "content": "Customer mentioned interest in premium plan",
      "author_id": "user@example.com",
      "created_at": "2024-11-05T12:00:00+00:00",
      "updated_at": "2024-11-05T12:00:00+00:00"
    }
  ],
  "total": 5,
  "page": 0,
  "page_size": 100
}

Note: Results ordered by newest first

Errors:
  - 404 Not Found: Lead doesn't exist
```

### Get Single Note
```
GET /notes/note/{note_id}

Response: 200 OK
{
  "id": 1,
  "lead_id": 42,
  "content": "Customer mentioned interest in premium plan",
  "author_id": "user@example.com",
  "created_at": "2024-11-05T12:00:00+00:00",
  "updated_at": "2024-11-05T12:00:00+00:00"
}

Errors:
  - 404 Not Found: Note doesn't exist
```

### Create Note
```
POST /notes/{lead_id}/notes
Content-Type: application/json

Request:
{
  "content": "Customer mentioned interest in premium plan",
  "author_id": "user@example.com"
}

Response: 201 Created
{
  "id": 1,
  "lead_id": 42,
  "content": "Customer mentioned interest in premium plan",
  "author_id": "user@example.com",
  "created_at": "2024-11-05T12:00:00+00:00",
  "updated_at": "2024-11-05T12:00:00+00:00"
}

Errors:
  - 404 Not Found: Lead doesn't exist
  - 422 Unprocessable Entity: Content is required
```

### Update Note
```
PUT /notes/{note_id}
Content-Type: application/json

Request (all fields optional):
{
  "content": "Updated note content",
  "author_id": "manager@example.com"
}

Response: 200 OK
{
  "id": 1,
  "lead_id": 42,
  "content": "Updated note content",
  "author_id": "manager@example.com",
  "created_at": "2024-11-05T12:00:00+00:00",
  "updated_at": "2024-11-05T12:30:00+00:00"
}

Note: updated_at is automatically updated to current time

Errors:
  - 404 Not Found: Note doesn't exist
```

### Delete Note
```
DELETE /notes/{note_id}

Response: 200 OK
{
  "message": "Note deleted successfully"
}

Errors:
  - 404 Not Found: Note doesn't exist
```

## Common Use Cases

### Workflow: Add tags to newly qualified lead
```bash
# 1. Get the lead (assume ID is 42)
# 2. Create or get tags
curl -X POST http://localhost:8000/api/v1/tags \
  -H "Content-Type: application/json" \
  -d '{"name": "qualified", "color": "#4CAF50", "category": "status"}'

# 3. Add tag to lead (by ID)
curl -X POST http://localhost:8000/api/v1/tags/42/tags \
  -H "Content-Type: application/json" \
  -d '{"tag_id": 5}'

# Or by name (auto-creates if needed)
curl -X POST http://localhost:8000/api/v1/tags/42/tags/by-name \
  -H "Content-Type: application/json" \
  -d '{"name": "qualified", "color": "#4CAF50", "category": "status"}'
```

### Workflow: Document lead interaction
```bash
# Create note
curl -X POST http://localhost:8000/api/v1/notes/42/notes \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Called at 2:30pm, discussed pricing. Agreed to follow-up meeting next week.",
    "author_id": "sales_rep@company.com"
  }'

# Update note with follow-up
curl -X PUT http://localhost:8000/api/v1/notes/1 \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Called at 2:30pm, discussed pricing. Agreed to follow-up meeting next week. Follow-up: Sent calendar invite.",
    "author_id": "sales_rep@company.com"
  }'
```

### Workflow: Find all hot leads
```bash
# Get tags (find hot_lead tag ID)
curl "http://localhost:8000/api/v1/tags?search=hot"

# Then use the lead-filtering endpoints (when implemented)
# to find all leads with specific tag
```

## Error Response Format

All errors follow standard HTTP status codes and return:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common Status Codes:
- `200 OK` - Successful GET/PUT/DELETE
- `201 Created` - Successful POST
- `400 Bad Request` - Invalid request format
- `404 Not Found` - Resource doesn't exist
- `409 Conflict` - Duplicate or conflicting data
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Database or server error

## Color Format

Tag colors must be valid hex color codes:
- 3-digit format: `#RGB` (e.g., `#F00` for red)
- 6-digit format: `#RRGGBB` (e.g., `#FF0000` for red)

Valid examples:
- `#FF6B6B` - Red
- `#4CAF50` - Green
- `#2196F3` - Blue
- `#FFC107` - Yellow
- `#9C27B0` - Purple
- `#808080` - Gray (default)

---

**Last Updated:** November 5, 2024
