# Entity Extraction Feature

## Overview

The entity extraction feature automatically extracts and stores information about users from their chat messages. This enables the chatbot to build a knowledge base about each user over time, including their preferences, usage patterns, personal information, and more.

## Features

### Extracted Entity Types

The system extracts the following types of information:

1. **name** - First names, last names, full names
2. **personal_info** - Age, location, occupation, education, family info
3. **preferences** - Likes, dislikes, interests, hobbies
4. **usage** - Technologies, tools, software, programming languages, frameworks
5. **goals** - Things users want to achieve or learn
6. **experience** - User's experience level with various topics
7. **contact** - Phone numbers, social media handles (excluding email)
8. **other** - Any other relevant personal information

### How It Works

1. **Automatic Extraction**: When a user sends a message, the system automatically analyzes it using an LLM-powered entity extractor
2. **Intelligent Processing**: Uses GPT-4o-mini with low temperature (0.1) for consistent and accurate extraction
3. **Contextual Storage**: Each entity is stored with context about where/how it was mentioned
4. **Session Tracking**: Entities are linked to both users and specific chat sessions
5. **Real-time Display**: Extracted entities are displayed in the UI panel in real-time

### UI Features

The entities panel on the right side of the interface shows:

- **Total Count**: Number of entities extracted for the user
- **Filter Options**: Filter by entity type (All, Name, Usage, Preferences, Info)
- **Color Coding**: Each entity type has a unique color for easy identification
- **Context Display**: Shows the context in which the entity was mentioned
- **Timestamp**: When each entity was extracted

### API Endpoints

#### Get All User Entities
```
GET /api/v1/entities/entities
Authorization: Bearer <user_token>
Query Parameters:
  - entity_type (optional): Filter by specific entity type
```

#### Get Session Entities
```
GET /api/v1/entities/entities/session/{session_id}
Authorization: Bearer <user_token>
```

#### Delete Entity
```
DELETE /api/v1/entities/entities/{entity_id}
Authorization: Bearer <user_token>
```

## Database Schema

```sql
CREATE TABLE user_entity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_value TEXT NOT NULL,
    context TEXT,
    confidence REAL NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);
```

## Migration

To add the entity extraction feature to an existing database:

```bash
sqlite3 your_database.db < scripts/migrate_entities.sql
```

Or for PostgreSQL, run the SQL commands from `schema.sql`.

## Configuration

No additional configuration is required. The entity extractor uses the same `LLM_API_KEY` configured for the main chatbot.

## Performance Considerations

- Entity extraction runs asynchronously and doesn't block chat responses
- Uses a lightweight model (gpt-4o-mini) to minimize costs
- Extraction failures don't affect chat functionality
- Entities are cached in the frontend to minimize API calls

## Privacy & Data Management

- All entities are user-scoped and private
- Users cannot see other users' entities
- Entities are automatically deleted when a user is deleted (CASCADE)
- Future enhancement: Add UI controls for users to delete individual entities

## Example Usage

**User Message:**
```
Hi, my name is Alice and I'm a Python developer who loves machine learning. I'm based in San Francisco.
```

**Extracted Entities:**
- Type: `name`, Value: `Alice`, Context: "user introduced themselves"
- Type: `usage`, Value: `Python`, Context: "programming language they use"
- Type: `preferences`, Value: `machine learning`, Context: "area of interest"
- Type: `personal_info`, Value: `San Francisco`, Context: "user's location"

## Future Enhancements

- [ ] Entity deduplication (avoid storing the same entity multiple times)
- [ ] Entity updating (update existing entities with new information)
- [ ] Entity confidence scoring (track how confident we are about each entity)
- [ ] User controls to edit/delete entities from the UI
- [ ] Entity-based personalization of chatbot responses
- [ ] Export entities as JSON for user download

