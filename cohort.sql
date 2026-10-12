-- Aggregate first; left join onto every HC-256 person to preserve non-users.
-- Negative/missing target payments and duplicate IDs are rejected before SQL.
WITH rx AS (
  SELECT DUPERSID,
    MAX(primary_flag) AS user,
    SUM(CASE WHEN primary_flag=1 THEN RXSF24X ELSE 0 END) AS oop,
    SUM(CASE WHEN primary_flag=1 THEN RXXP24X ELSE 0 END) AS total,
    SUM(primary_flag) AS fills,
    MAX(CASE WHEN ingredient='semaglutide' THEN 1 ELSE 0 END) AS semaglutide_user,
    SUM(CASE WHEN ingredient='semaglutide' THEN RXSF24X ELSE 0 END) AS semaglutide_oop,
    SUM(CASE WHEN ingredient='semaglutide' THEN RXXP24X ELSE 0 END) AS semaglutide_total,
    SUM(CASE WHEN ingredient='semaglutide' THEN 1 ELSE 0 END) AS semaglutide_fills,
    MAX(CASE WHEN ingredient='tirzepatide' THEN 1 ELSE 0 END) AS tirzepatide_user,
    SUM(CASE WHEN ingredient='tirzepatide' THEN RXSF24X ELSE 0 END) AS tirzepatide_oop,
    SUM(CASE WHEN ingredient='tirzepatide' THEN RXXP24X ELSE 0 END) AS tirzepatide_total,
    SUM(CASE WHEN ingredient='tirzepatide' THEN 1 ELSE 0 END) AS tirzepatide_fills,
    MAX(brand_flag) AS brand_user,
    SUM(CASE WHEN brand_flag=1 THEN RXSF24X ELSE 0 END) AS brand_oop,
    SUM(CASE WHEN brand_flag=1 THEN RXXP24X ELSE 0 END) AS brand_total,
    SUM(brand_flag) AS brand_fills
  FROM events GROUP BY DUPERSID
)
SELECT p.*,
  COALESCE(r.user,0) AS user, COALESCE(r.oop,0) AS oop,
  COALESCE(r.total,0) AS total, COALESCE(r.fills,0) AS fills,
  COALESCE(r.semaglutide_user,0) AS semaglutide_user,
  COALESCE(r.semaglutide_oop,0) AS semaglutide_oop,
  COALESCE(r.semaglutide_total,0) AS semaglutide_total,
  COALESCE(r.semaglutide_fills,0) AS semaglutide_fills,
  COALESCE(r.tirzepatide_user,0) AS tirzepatide_user,
  COALESCE(r.tirzepatide_oop,0) AS tirzepatide_oop,
  COALESCE(r.tirzepatide_total,0) AS tirzepatide_total,
  COALESCE(r.tirzepatide_fills,0) AS tirzepatide_fills,
  COALESCE(r.brand_user,0) AS brand_user, COALESCE(r.brand_oop,0) AS brand_oop,
  COALESCE(r.brand_total,0) AS brand_total, COALESCE(r.brand_fills,0) AS brand_fills
FROM persons p LEFT JOIN rx r ON p.DUPERSID=r.DUPERSID
ORDER BY p.DUPERSID;
