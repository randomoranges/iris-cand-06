-- 013_screening.sql — the fully-clean PASS dataset (the happy-path contrast case).
-- Every row is valid on every check, so screening promotes with no warnings.
INSERT INTO screening (screening_id, country_code, region_code, eco_points_per_m2, source_date, geom) VALUES
  ('DE-SCR-01', 'DE', 'DE-NW', 8, DATE '2026-02-01',
     ST_GeomFromText('POLYGON((6.9 51.4, 7.0 51.4, 7.0 51.5, 6.9 51.5, 6.9 51.4))', 4326)),
  ('DE-SCR-02', 'DE', 'DE-NW', 8, DATE '2026-02-01',
     ST_GeomFromText('POLYGON((7.1 51.4, 7.2 51.4, 7.2 51.5, 7.1 51.5, 7.1 51.4))', 4326)),
  ('DE-SCR-03', 'DE', 'DE-NW', 8, DATE '2026-02-01',
     ST_GeomFromText('MULTIPOLYGON(((7.3 51.4, 7.4 51.4, 7.4 51.5, 7.3 51.5, 7.3 51.4)))', 4326)),
  ('DE-SCR-04', 'DE', 'DE-NW', 8, DATE '2026-02-01',
     ST_GeomFromText('POLYGON((6.7 51.4, 6.8 51.4, 6.8 51.5, 6.7 51.5, 6.7 51.4))', 4326));
