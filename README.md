# IRIS QA Gate

This is my go at the IRIS candidate task (IRIS-CAND-06). It's a small quality gate
that looks at incoming geospatial datasets before they're allowed through, and tells
you plainly whether each one is good to go, worth a second glance, or has to be
stopped.

Stack: Python 3.12+ and PostgreSQL 16 with PostGIS 3.4, run through Docker.

## What the task asked for

The brief was to build a QA framework that runs different acceptance checks on four
kinds of data: parcels, substations, peatland, and screening layers. Before anything
gets promoted it has to catch the usual problems — broken geometry, bad keys, wrong
country, duplicates, stale dates. Some of those are hard stops, some are just worth
flagging, and optional missing data should stay visible without holding everything up.

They also asked for the checks to be split across SQL and Python, for the run summary
to be saved somewhere, and for tests and an example report.

## How I read it

The thing that made the whole design click was one idea: whether a problem is a
"block" or just a "warning" isn't really about the check, it's about the dataset. A
missing field is a hard stop on a parcel's geometry, but a missing soil reading on
peatland is only worth flagging. Same underlying check, different meaning depending
on where it runs.

So I split it three ways. A check only knows how to find one kind of problem and
report what it found. A profile (one per dataset) says which checks apply and how
serious each one is there. A small engine runs the checks and works out the verdict.
That's the part I'd point to if someone asked what makes it reusable — adding a new
dataset is a new profile, and changing how strict a dataset is means flipping one
setting, without touching any check code.

Every check lands on one of three outcomes:

- **PASS** — nothing wrong.
- **WARN** — not perfect, but fine to promote. Stays visible so nobody forgets about it.
- **BLOCK** — something's actually broken, so promotion is held.

A dataset's overall verdict is just the worst thing found in it. It promotes unless
something blocks.

## About the data

There's no real IRIS data in here, and the task didn't want any. I generated fake but
plausible data with AI and committed it as fixtures (the `.sql` files under
`db/fixtures/`). Each dataset has a few clean rows plus some deliberately broken ones,
so every check has something to catch. The coordinates sit around Cologne / NRW and
are made up.

Here's what's in each dataset:

- **parcels** — land plots (polygons). This is the strict one. I put in duplicate keys,
  a self-crossing "bowtie" polygon, a wrong coordinate system, a missing geometry, a
  null country, a foreign country, and one row that's broken two ways at once.
- **substations** — power substations (points). Includes a polygon that shouldn't be
  there (wrong shape), a wrong coordinate system, a null country, and a foreign one.
- **peatland** — soil polygons. Structurally these are all fine; what some rows are
  missing is the optional soil-depth reading or the source date. Those warn, they
  don't block. That's really the point of this dataset.
- **screening** — commercial suitability polygons. All clean, so it passes with nothing
  flagged. It's the happy-path example, and it's what proves a good dataset sails
  through.

## The checks

| Check | Runs in | What it catches |
|---|---|---|
| `required_fields` | Python | a contracted field is null |
| `country_scope` | Python | country is null or not the one we expect |
| `source_date` | Python | missing source date (warns) |
| `optional_soil_attribute` | Python | missing optional enrichment (warns) |
| `eco_points_present` | Python | missing eco-points on screening (warns) |
| `key_uniqueness` | SQL | duplicated business keys |
| `duplicate_rows` | SQL | fully identical rows |
| `geometry_valid` | SQL (`ST_IsValid`) | self-intersections and other invalid shapes |
| `geometry_type` | SQL (`GeometryType`) | wrong shape (e.g. a polygon where a point belongs) |
| `geometry_srid` | SQL (`ST_SRID`) | wrong coordinate system |

The geometry and duplicate work happens in SQL, since that's what PostGIS is good at.
The field-level stuff (required fields, country, dates) happens in Python. So the
"at least one in SQL, one in Python" requirement is covered several times over.

## Running it

You need two things installed: **Docker** (it runs the database for you, PostGIS and
everything) and **Python 3.12+**. You do not need to install Postgres or PostGIS
yourself — that comes inside the Docker image.

```bash
# 1. Start the database
docker compose up -d

# 2. Make an isolated Python environment and install the tool
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# 3. Load the schema and the fixtures
qa init-db

# 4. Run the gate over everything
qa run --all

# 5. Run the tests
pytest -q
```

`make up init run test` wraps the same steps if you prefer.

On an Apple Silicon Mac, Docker may warn that the image is built for Intel. It's
harmless — the image runs under emulation and the container reports healthy.

## Where the results show up

The same run lands in three places, so you can look at it however suits you:

- **Terminal** — a verdict per dataset, and under each one the checks that failed with
  a short reason and an example row.
- **`reports/qa_report.html`** — open it in a browser for the nice view: every dataset,
  every check, colour-coded, with the reason and evidence for anything that failed.
- **`reports/<dataset>_qa_report.json`** — the full detail per dataset (passes included),
  handy for attaching to a ticket.
- **Postgres** — the `qa_run` and `qa_run_check` tables keep a history you can query.

`qa run` also exits with code 2 if anything blocked, so it can fail a CI or promotion
step. PASS and WARN both exit 0.

## Tests

`pytest -q` runs 48 tests. Four of them are the exact acceptance criteria from the
brief (block vs warn is distinguishable, a missing soil attribute warns without
blocking, a malformed parcel geometry blocks, duplicate keys block deterministically).
The rest pin down every check on every dataset, plus the core outcome logic, which
runs without a database at all.

## Assumptions and shortcuts I made

A few things I kept simple on purpose:

- I didn't put a `UNIQUE` constraint on the business keys. The gate's whole job is to
  *spot* bad incoming data, so the tables have to be able to hold duplicates and
  malformed geometry. Correctness is judged by the checks, not blocked at insert.
- `required_fields` and `country_scope` both flag a null country. That's on purpose —
  one is checking "is it filled in", the other "is it the right country". Either way
  it blocks; seeing both just helps when you're diagnosing.
- Country scope is a single expected code per dataset (`DE` here). Fine for a
  one-region pilot; a real setup would use a list per dataset.
- `source_date` only checks that a date is there, not how old it is.
- The fixtures are small and synthetic, sized to exercise each check.

## If I were taking this further

| Shortcut now | What I'd do for production |
|---|---|
| source_date only checks presence | add a max-age rule per dataset |
| duplicates listed in the report | move the offending rows to a real quarantine table |
| one expected country per dataset | per-dataset country allow-lists |
| fixtures loaded by the CLI | proper ingestion adapters per source, same profiles |
| you run `qa run` by hand | wire the exit code into the promotion pipeline |

## Project layout

```
docker-compose.yml             PostGIS 16-3.4 service
db/migrations/001_schema.sql   tables + the qa_run summary tables
db/fixtures/*.sql              the synthetic data (clean + broken rows)
qa/contracts.py                the outcome model (PASS/WARN/BLOCK)
qa/target.py                   what a check needs to know about a dataset
qa/checks/                     sql_checks.py + python_checks.py
qa/profiles.py                 the four rulebooks (severity per dataset)
qa/engine.py                   runs a profile, works out the verdict
qa/persist.py                  writes JSON + saves to Postgres
qa/report_html.py              builds the HTML dashboard
qa/cli.py                      the `qa init-db` / `qa run` commands
tests/                         acceptance + full per-check matrix + logic tests
reports/                       example JSON + HTML output (regenerated by a run)
```
