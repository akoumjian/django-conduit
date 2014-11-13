#!/bin/bash
set -ev

#if [ "${DJANGO}" = "1.4" ]; then
#    #  do it the manual way
#else
#    psql -c 'create database geoexample;' -U postgres
#    psql -U postgres -d geoexample -c "create extension postgis"
#fi

createdb -U postgres -E UTF8 template_postgis
# allow non-superusers the ability to create from this template
psql -U postgres -d postgres -c "UPDATE pg_database SET datistemplate='true' WHERE datname='template_postgis';"
psql -U postgres -d template_postgis -c "create extension postgis;"
# enable users to alter spatial tables.
psql -U postgres -d template_postgis -c "GRANT ALL ON geometry_columns TO PUBLIC;"
psql -U postgres -d template_postgis -c "GRANT ALL ON geography_columns TO PUBLIC;"
psql -U postgres -d template_postgis -c "GRANT ALL ON spatial_ref_sys TO PUBLIC;"
# create geoexample from this template
createdb -T template_postgis -O postgres geoexample 
