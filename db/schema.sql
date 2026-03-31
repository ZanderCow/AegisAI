-- Initial schema for AegisAI
CREATE TABLE IF NOT EXISTS users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email         VARCHAR(320) NOT NULL UNIQUE,
  hashed_password VARCHAR(255) NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  role              VARCHAR(20) NOT NULL DEFAULT 'user'
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

CREATE TABLE IF NOT EXISTS conversations (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  display_id    BIGSERIAL NOT NULL UNIQUE,
  title         VARCHAR(255) NOT NULL DEFAULT 'New Chat',
  user_id       UUID NOT NULL REFERENCES users(id),
  provider      VARCHAR(50) NOT NULL,
  model         VARCHAR(100) NOT NULL,
  tokens_used   BIGINT NOT NULL DEFAULT 0,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  display_id        BIGSERIAL NOT NULL UNIQUE,
  conversation_id   UUID NOT NULL REFERENCES conversations(id),
  role              VARCHAR(20) NOT NULL,
  content           TEXT NOT NULL,
  token_count       INTEGER,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alarm (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id        UUID NOT NULL REFERENCES messages(id),
  reason            TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations (user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages (conversation_id);
CREATE INDEX IF NOT EXISTS idx_alarms_message_id ON alarm (message_id);
