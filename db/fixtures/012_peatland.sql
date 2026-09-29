-- 012_peatland.sql — the WARN dataset.
-- Every row is structurally valid (valid geom, right type, right SRID, non-null in-scope
-- country, unique keys), so nothing here BLOCKS. The only issues are missing OPTIONAL
-- enrichment -> WARN, proving optional gaps stay visible without holding promotion.
INSERT INTO peatland (peatland_id, country_code, region_code, peat_depth_m, source_date, geom) VALUES
  -- fully enriched, clean
  ('DE-PEAT-01', 'DE', 'DE-NW', 3.2, DATE '2025-08-01',
     ST_GeomFromText('POLYGON((6.9 51.2, 7.0 51.2, 7.0 51.3, 6.9 51.3, 6.9 51.2))', 4326)),
  -- fully enriched, clean
  ('DE-PEAT-02', 'DE', 'DE-NW', 2.1, DATE '2025-08-01',
     ST_GeomFromText('POLYGON((7.1 51.2, 7.2 51.2, 7.2 51.3, 7.1 51.3, 7.1 51.2))', 4326)),
  -- clean MULTIPOLYGON (multipolygon accepted)
  ('DE-PEAT-03', 'DE', 'DE-NW', 1.5, DATE '2025-08-01',
     ST_GeomFromText('MULTIPOLYGON(((7.3 51.2, 7.4 51.2, 7.4 51.3, 7.3 51.3, 7.3 51.2)))', 4326)),
  -- WARN: missing optional soil attribute (peat_depth_m IS NULL) -> stays visible as unknown
  ('DE-PEAT-04', 'DE', 'DE-NW', NULL, DATE '2025-08-01',
     ST_GeomFromText('POLYGON((6.5 51.2, 6.6 51.2, 6.6 51.3, 6.5 51.3, 6.5 51.2))', 4326)),
  -- WARN: missing source_date (freshness unknown)
  ('DE-PEAT-05', 'DE', 'DE-NW', 2.0, NULL,
     ST_GeomFromText('POLYGON((6.7 51.2, 6.8 51.2, 6.8 51.3, 6.7 51.3, 6.7 51.2))', 4326)),
  -- WARN x2: missing BOTH soil attribute and source_date
  ('DE-PEAT-06', 'DE', 'DE-NW', NULL, NULL,
     ST_GeomFromText('POLYGON((7.5 51.2, 7.6 51.2, 7.6 51.3, 7.5 51.3, 7.5 51.2))', 4326)),
  -- fully enriched, clean
  ('DE-PEAT-07', 'DE', 'DE-NW', 4.0, DATE '2025-08-01',
     ST_GeomFromText('POLYGON((7.7 51.2, 7.8 51.2, 7.8 51.3, 7.7 51.3, 7.7 51.2))', 4326));
