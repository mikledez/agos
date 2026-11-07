CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL CHECK (email <> ''),
    name TEXT,
    image TEXT,
    email_verified TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id INT,
    name TEXT NOT NULL CHECK (name <> ''),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (parent_id IS NULL OR parent_id != id),
    UNIQUE (id, user_id),
    CONSTRAINT sessions_parent_same_user_fk
        FOREIGN KEY (parent_id, user_id)
        REFERENCES sessions(id, user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_parent ON sessions(user_id, parent_id);
CREATE INDEX IF NOT EXISTS idx_sessions_parent ON sessions(parent_id);

CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id INT,
    original_filename TEXT NOT NULL,
    stored_filename TEXT NOT NULL,
    annotated_path TEXT,
    phase TEXT NOT NULL CHECK (phase IN ('toe_off', 'mid_stance', 'touchdown')),
    direction TEXT NOT NULL CHECK (direction IN ('ltr', 'rtl')),
    swing_hip FLOAT, swing_knee FLOAT, swing_ankle FLOAT,
    stance_hip FLOAT, stance_knee FLOAT, stance_ankle FLOAT,
    thigh_thigh FLOAT,
    feedback TEXT,
    swing_feedback TEXT,
    stance_feedback TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (id, user_id),
    UNIQUE (user_id, stored_filename),
    CONSTRAINT images_session_same_user_fk
        FOREIGN KEY (session_id, user_id)
        REFERENCES sessions(id, user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_images_user ON images(user_id);
CREATE INDEX IF NOT EXISTS idx_images_session ON images(session_id);
CREATE INDEX IF NOT EXISTS idx_images_user_session ON images(user_id, session_id);
CREATE INDEX IF NOT EXISTS idx_images_phase ON images(phase);

CREATE TABLE IF NOT EXISTS image_files (
    image_id INT PRIMARY KEY,
    user_id INT NOT NULL,
    original BYTEA NOT NULL,
    annotated BYTEA,
    CONSTRAINT image_files_image_same_user_fk
        FOREIGN KEY (image_id, user_id)
        REFERENCES images(id, user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS image_humanizations (
    id SERIAL PRIMARY KEY,
    image_id INT NOT NULL UNIQUE,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    model TEXT NOT NULL CHECK (model <> ''),
    prompt TEXT,
    humanized_text TEXT NOT NULL CHECK (humanized_text <> ''),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT humanizations_image_same_user_fk
        FOREIGN KEY (image_id, user_id)
        REFERENCES images(id, user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_humanizations_image ON image_humanizations(image_id);
CREATE INDEX IF NOT EXISTS idx_humanizations_user ON image_humanizations(user_id);

CREATE TABLE IF NOT EXISTS image_chat_messages (
    id SERIAL PRIMARY KEY,
    image_id INT NOT NULL,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL CHECK (content <> ''),
    model TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chat_image_same_user_fk
        FOREIGN KEY (image_id, user_id)
        REFERENCES images(id, user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chat_image_created
    ON image_chat_messages(image_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chat_user
    ON image_chat_messages(user_id);

CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS users_set_updated_at ON users;
CREATE TRIGGER users_set_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS sessions_set_updated_at ON sessions;
CREATE TRIGGER sessions_set_updated_at
    BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS images_set_updated_at ON images;
CREATE TRIGGER images_set_updated_at
    BEFORE UPDATE ON images
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

DROP TRIGGER IF EXISTS image_humanizations_set_updated_at ON image_humanizations;
CREATE TRIGGER image_humanizations_set_updated_at
    BEFORE UPDATE ON image_humanizations
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
