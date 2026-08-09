# Telegram Integration

Atlas AI's Telegram integration is implemented as a FastAPI webhook adapter that reuses the existing `User`, `Conversation`, `ChatService`, and AI orchestration stack.

## Architecture

```text
Telegram update
  -> POST /telegram/webhook
  -> TelegramService
  -> existing User via telegram_user_id
  -> existing Conversation
  -> existing ChatService
  -> existing AI Orchestrator
  -> RAG / finance / tools
  -> TelegramClient.send_message
```

The webhook does not call the LLM directly and does not maintain a second conversation or history system.

## Configuration

Use the existing nested settings system.

```env
TELEGRAM__BOT_TOKEN=
TELEGRAM__WEBHOOK_SECRET=
TELEGRAM__REQUEST_TIMEOUT_SECONDS=10.0
```

Keep real values only in `.env`. The repository ignores `.env` and `.env.*` except `.env.example`.

## Account Linking

Telegram accounts are linked to existing Atlas users through the existing `telegram_user_id` field on `users`.

Linking flow:

1. Sign in to Atlas with the normal authentication flow.
2. Call `POST /auth/telegram/link-token` with a bearer token.
3. Send `/link <token>` to the Telegram bot.

The link token is short-lived and signed by the existing JWT secret. The bot never trusts a free-form user ID supplied by Telegram chat text.

## Webhook Security

If `TELEGRAM__WEBHOOK_SECRET` is configured, the webhook expects the `X-Telegram-Bot-Api-Secret-Token` header used by Telegram webhook requests. Invalid or missing secrets are rejected.

## Supported Behavior

- Private chats only
- `/start`
- `/link <token>`
- Multi-turn chat through the existing `ChatService`
- Existing RAG and finance capabilities through the normal orchestrator path

## Limitations

- Group and supergroup chats are not supported
- Voice, image, sticker, and callback updates are not processed beyond safe rejection or ignore handling
- The initial implementation reuses one persistent private Telegram conversation per Atlas user

## Local Development

Telegram webhooks require a publicly reachable HTTPS endpoint. Local testing generally uses a development tunnel or a deployed environment. The application does not automatically register a production webhook URL.

## Testing

Tests use fake Telegram clients and fake chat services. No test should call the real Telegram Bot API or include a real bot token.