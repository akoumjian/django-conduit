#!/bin/bash
set -ev

#if [ "${DJANGO}" = "1.4" ]; then
#    #  do it the manual way
#else
#    psql -c 'create database geoexample;' -U postgres
#    psql -U postgres -d geoexample -c "create extension postgis"
#fi

# print environment variables
env

POSTGIS_SQL_PATH=`pg_config --sharedir`/contrib/postgis-2.0
# Creating the template spatial database.
createdb -U postgres -E UTF8 template_postgis
createlang -U postgres -d template_postgis plpgsql # Adding PLPGSQL language support.
# Allows non-superusers the ability to create from this template
psql -U postgres -d postgres -c "UPDATE pg_database SET datistemplate='true' WHERE datname='template_postgis';"
# Loading the PostGIS SQL routines
psql -U postgres -d template_postgis -f $POSTGIS_SQL_PATH/postgis.sql 
psql -U postgres -d template_postgis -f $POSTGIS_SQL_PATH/spatial_ref_sys.sql
# Enabling users to alter spatial tables.
psql -U postgres -d template_postgis -c "GRANT ALL ON geometry_columns TO PUBLIC;"
psql -U postgres -d template_postgis -c "GRANT ALL ON geography_columns TO PUBLIC;"
psql -U postgres -d template_postgis -c "GRANT ALL ON spatial_ref_sys TO PUBLIC;"
# create geoexample from this template
createdb -T template_postgis -O postgres geoexample 
