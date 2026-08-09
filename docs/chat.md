# Chat API

Atlas AI's chat API requires a bearer JWT and uses the active `app.core.config` settings system. Configure credentials through a local `.env` file; `.env` is ignored by Git.

```env
OPENAI__API_KEY=your_key_here
OPENAI__MODEL=openai/gpt-oss-20b
OPENAI__BASE_URL=https://api.groq.com/openai/v1
AUTH__JWT_SECRET_KEY=replace_with_a_strong_secret
CHAT__HISTORY_LIMIT=20
```

Start the API with `uv run uvicorn app.main:app --reload`. Use `POST /auth/token` to obtain a development token for an existing user, then call `POST /chat` with an `Authorization: Bearer <token>` header.

The request body accepts `text`, optional `conversation_id`, and optional metadata. Text must be non-blank and no longer than 8,000 characters. Each successful response includes the conversation, user-message, and assistant-message IDs. Use the conversation endpoints to retrieve bounded chronological messages or delete an owned conversation.

Conversation access is ownership-safe: an unavailable or another user's conversation returns 404. Chat preserves the submitted user message if the provider later fails, then returns a controlled 503 without exposing provider internals.

Normal automated tests inject a fake orchestrator and do not call the external LLM provider.
