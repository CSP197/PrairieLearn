CREATE TABLE IF NOT EXISTS topics (
    id BIGSERIAL PRIMARY KEY,
    name text,
    number INTEGER,
    color text,
    course_id BIGINT NOT NULL REFERENCES courses ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE (name, course_id)
);

ALTER TABLE topics ALTER COLUMN id SET DATA TYPE BIGINT;
ALTER TABLE topics ALTER COLUMN course_id SET DATA TYPE BIGINT;
ALTER TABLE topics ALTER COLUMN name SET DATA TYPE TEXT;
ALTER TABLE topics ALTER COLUMN color SET DATA TYPE TEXT;
