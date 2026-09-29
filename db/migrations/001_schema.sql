-- 001_schema.sql
-- IRIS QA Gate — schema migration.
-- Idempotent: safe to run repeatedly (used by `qa init-db`).
--
-- Design contracts enforced here:
--   * Every business entity carries a NON-NULL country_code (country-scoped identity).
--   * Canonical geometry column is named `geom` (never invented if absent).
--   * A per-dataset natural/business key exists and is what "key uniqueness" checks.
--   * source_date is an explicit freshness contract column (nullable -> warns, never invented).

CREATE EXTENSION IF NOT EXISTS postgis;

------------------------------------------------------------------------
-- Dataset tables (the things being screened before promotion)
------------------------------------------------------------------------

-- Parcels: land plots. Expected geometry: polygon, SRID 4326.
DROP TABLE IF EXISTS parcels CASCADE;
CREATE TABLE parcels (
    row_id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,  -- surrogate load id
    parcel_id    text,                 -- business key (uniqueness is checked, not DB-enforced,
                                        -- so malformed inbound data is observable rather than rejected at insert)
    country_code text,                 -- contract: must be non-null + in scope
    region_code  text,
    source_date  date,                 -- freshness contract
    geom         geometry              -- canonical geometry column
);

-- Substations: point infrastructure. Expected geometry: point, SRID 4326.
DROP TABLE IF EXISTS substations CASCADE;
CREATE TABLE substations (
    row_id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    substation_id text,
    country_code  text,
    region_code   text,
    capacity_mva  numeric,
    source_date   date,
    geom          geometry
);

-- Peatland: soil polygons. Carries an OPTIONAL enrichment attribute (peat_depth_m):
-- missing enrichment WARNS (stays visible as unknown) but must NOT block.
DROP TABLE IF EXISTS peatland CASCADE;
CREATE TABLE peatland (
    row_id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    peatland_id  text,
    country_code text,
    region_code  text,
    peat_depth_m numeric,              -- OPTIONAL soil enrichment (nullable -> warn)
    source_date  date,
    geom         geometry
);

-- Screening: commercial site-suitability layer. Expected geometry: polygon, SRID 4326.
-- eco_points_per_m2 is the indicative commercial factor (baseline 8, per project wording).
DROP TABLE IF EXISTS screening CASCADE;
CREATE TABLE screening (
    row_id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    screening_id      text,
    country_code      text,
    region_code       text,
    eco_points_per_m2 numeric,
    source_date       date,
    geom              geometry
);

------------------------------------------------------------------------
-- QA result tables (the persisted run summary)
------------------------------------------------------------------------

-- One row per QA run over one dataset.
-- country_code here is the SCOPE of the run — honouring the "non-null country_code
-- on every persisted entity" contract for QA artefacts too.
DROP TABLE IF EXISTS qa_run_check CASCADE;
DROP TABLE IF EXISTS qa_run CASCADE;

CREATE TABLE qa_run (
    run_id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset         text        NOT NULL,
    country_code    text        NOT NULL,
    overall_outcome text        NOT NULL,          -- PASS | WARN | BLOCK
    promoted        boolean     NOT NULL,          -- allowed to move forward?
    row_count       integer     NOT NULL,
    started_at      timestamptz NOT NULL DEFAULT now()
);

-- One row per check within a run, with machine-readable evidence.
CREATE TABLE qa_run_check (
    id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id       bigint      NOT NULL REFERENCES qa_run(run_id) ON DELETE CASCADE,
    check_name   text        NOT NULL,
    kind         text        NOT NULL,             -- sql | python
    severity     text        NOT NULL,             -- BLOCK | WARN  (what a failure escalates to)
    outcome      text        NOT NULL,             -- PASS | WARN | BLOCK
    failed_count integer     NOT NULL,
    evidence     jsonb       NOT NULL DEFAULT '[]'::jsonb
);
