-- 011_substations.sql — substation (point) fixtures covering every substation case.
INSERT INTO substations (substation_id, country_code, region_code, capacity_mva, source_date, geom) VALUES
  -- clean point
  ('DE-SUB-01', 'DE', 'DE-NW', 40, DATE '2025-11-01',
     ST_GeomFromText('POINT(6.95 51.05)', 4326)),
  -- clean point
  ('DE-SUB-02', 'DE', 'DE-NW', 25, DATE '2025-11-01',
     ST_GeomFromText('POINT(7.05 51.05)', 4326)),
  -- DEFECT: duplicate business key (same substation_id as DE-SUB-02) -> key_uniqueness
  ('DE-SUB-02', 'DE', 'DE-NW', 30, DATE '2025-11-01',
     ST_GeomFromText('POINT(7.15 51.05)', 4326)),
  -- DEFECT: null country_code -> required_fields + country_scope
  ('DE-SUB-03', NULL, 'DE-NW', 25, DATE '2025-11-01',
     ST_GeomFromText('POINT(7.25 51.05)', 4326)),
  -- DEFECT: out-of-scope country (FR) -> country_scope
  ('FR-SUB-04', 'FR', 'FR-GES', 25, DATE '2025-11-01',
     ST_GeomFromText('POINT(7.35 51.05)', 4326)),
  -- DEFECT: wrong geometry type (polygon in a point dataset) -> geometry_type
  ('DE-SUB-05', 'DE', 'DE-NW', 60, DATE '2025-11-01',
     ST_GeomFromText('POLYGON((6.9 51.0, 7.0 51.0, 7.0 51.1, 6.9 51.1, 6.9 51.0))', 4326)),
  -- DEFECT: wrong SRID -> geometry_srid
  ('DE-SUB-06', 'DE', 'DE-NW', 15, DATE '2025-11-01',
     ST_GeomFromText('POINT(6.85 51.05)', 25832)),
  -- DEFECT: geometry missing entirely (null) -> required_fields
  ('DE-SUB-07', 'DE', 'DE-NW', 20, DATE '2025-11-01', NULL),
  -- WARN: missing source_date -> source_date warns, does not block
  ('DE-SUB-08', 'DE', 'DE-NW', 35, NULL,
     ST_GeomFromText('POINT(6.75 51.05)', 4326));
