-- COPY (SELECT path,name,pcode FROM geo_adminarea) TO '/tmp/geo_adminarea.copy';
-- COPY (SELECT adminarea_ptr_id FROM geo_suco)  TO '/tmp/geo_suco.copy';
-- COPY (SELECT adminarea_ptr_id FROM geo_subdistrict)  TO '/tmp/geo_subdistrict.copy';
-- COPY (SELECT adminarea_ptr_id FROM geo_district)  TO '/tmp/geo_district.copy';

COPY geo_adminarea (path,name,pcode) FROM '/docker-entrypoint-initdb.d/geo_adminarea.copy';
COPY geo_suco(adminarea_ptr_id) FROM '/docker-entrypoint-initdb.d/geo_suco.copy';
COPY geo_subdistrict(adminarea_ptr_id)   FROM '/docker-entrypoint-initdb.d/geo_subdistrict.copy';
COPY geo_district(adminarea_ptr_id) FROM '/docker-entrypoint-initdb.d/geo_district.copy';
