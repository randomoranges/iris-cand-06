-- 010_parcels.sql — parcel fixtures covering every parcel case.
-- Each row is either clean or carries a labelled defect that a specific check catches.
INSERT INTO parcels (parcel_id, country_code, region_code, source_date, geom) VALUES
  -- clean polygon
  ('DE-P-0001', 'DE', 'DE-NW', DATE '2026-01-15',
     ST_GeomFromText('POLYGON((6.9 51.0, 7.0 51.0, 7.0 51.1, 6.9 51.1, 6.9 51.0))', 4326)),
  -- clean polygon
  ('DE-P-0002', 'DE', 'DE-NW', DATE '2026-01-15',
     ST_GeomFromText('POLYGON((7.1 51.0, 7.2 51.0, 7.2 51.1, 7.1 51.1, 7.1 51.0))', 4326)),
  -- clean MULTIPOLYGON (confirms multipolygon is an accepted type, not just polygon)
  ('DE-P-0003', 'DE', 'DE-NW', DATE '2026-01-15',
     ST_GeomFromText('MULTIPOLYGON(((6.9 51.6, 7.0 51.6, 7.0 51.7, 6.9 51.7, 6.9 51.6)))', 4326)),
  -- DEFECT: duplicate business key (same parcel_id as DE-P-0002, different geom) -> key_uniqueness
  ('DE-P-0002', 'DE', 'DE-NW', DATE '2026-01-15',
     ST_GeomFromText('POLYGON((7.3 51.0, 7.4 51.0, 7.4 51.1, 7.3 51.1, 7.3 51.0))', 4326)),
  -- DEFECT: fully-identical row pair (every business column equal) -> duplicate_rows (+ key_uniqueness)
  ('DE-P-0009', 'DE', 'DE-NW', DATE '2026-03-01',
     ST_GeomFromText('POLYGON((6.5 51.0, 6.6 51.0, 6.6 51.1, 6.5 51.1, 6.5 51.0))', 4326)),
  ('DE-P-0009', 'DE', 'DE-NW', DATE '2026-03-01',
     ST_GeomFromText('POLYGON((6.5 51.0, 6.6 51.0, 6.6 51.1, 6.5 51.1, 6.5 51.0))', 4326)),
  -- DEFECT: self-intersecting "bowtie" polygon -> geometry_valid
  ('DE-P-0004', 'DE', 'DE-NW', DATE '2026-01-15',
     ST_GeomFromText('POLYGON((6.9 51.0, 7.0 51.1, 7.0 51.0, 6.9 51.1, 6.9 51.0))', 4326)),
  -- DEFECT: wrong SRID (25832 instead of 4326) -> geometry_srid
  ('DE-P-0005', 'DE', 'DE-NW', DATE '2026-01-15',
     ST_GeomFromText('POLYGON((6.9 51.0, 7.0 51.0, 7.0 51.1, 6.9 51.1, 6.9 51.0))', 25832)),
  -- DEFECT: geometry missing entirely (null) -> required_fields (geometry checks skip nulls, don't crash)
  ('DE-P-0006', 'DE', 'DE-NW', DATE '2026-01-15', NULL),
  -- DEFECT: null country_code -> required_fields + country_scope
  ('DE-P-0007', NULL, 'DE-NW', DATE '2026-01-15',
     ST_GeomFromText('POLYGON((7.5 51.0, 7.6 51.0, 7.6 51.1, 7.5 51.1, 7.5 51.0))', 4326)),
  -- DEFECT: out-of-scope country (FR when scope is DE) -> country_scope
  ('FR-P-0008', 'FR', 'FR-GES', DATE '2026-01-15',
     ST_GeomFromText('POLYGON((7.7 51.0, 7.8 51.0, 7.8 51.1, 7.7 51.1, 7.7 51.0))', 4326)),
  -- WARN: missing source_date (freshness unknown) -> source_date warns, does not block
  ('DE-P-0010', 'DE', 'DE-NW', NULL,
     ST_GeomFromText('POLYGON((6.7 51.0, 6.8 51.0, 6.8 51.1, 6.7 51.1, 6.7 51.0))', 4326)),
  -- DEFECT: two problems at once (invalid geometry AND wrong SRID) -> geometry_valid + geometry_srid
  ('DE-P-0011', 'DE', 'DE-NW', DATE '2026-01-15',
     ST_GeomFromText('POLYGON((6.9 51.0, 7.0 51.1, 7.0 51.0, 6.9 51.1, 6.9 51.0))', 25832));
