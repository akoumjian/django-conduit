#!/bin/bash
set -ev

if [ "${DJANGO}" = "1.4" ]; then
    #  
    #  django 1.4 seems to require the existence
    #  of the default POSTGIS_VERSION=template_postgis
    #  shown here https://docs.djangoproject.com/en/dev/ref/contrib/gis/testing/.
    #  it will prompt the user on syncdb if it does not exist and
    #  this screws up Travis CI builds.
    #  so we do it the every manual way with a template to get around this.
    #  
    createdb -U postgres -E UTF8 template_postgis
    # spatially enable the template
    psql -U postgres -d template_postgis -c "create extension postgis;"
    # allow non-superusers the ability to create from this template
    psql -U postgres -d postgres -c "UPDATE pg_database SET datistemplate='true' WHERE datname='template_postgis';"
    # enable users to alter spatial tables.
    psql -U postgres -d template_postgis -c "GRANT ALL ON geometry_columns TO PUBLIC;"
    psql -U postgres -d template_postgis -c "GRANT ALL ON geography_columns TO PUBLIC;"
    psql -U postgres -d template_postgis -c "GRANT ALL ON spatial_ref_sys TO PUBLIC;"
    # create geoexample from this template
    createdb -T template_postgis -O postgres geoexample 
else
    #
    #  all other
    psql -c 'create database geoexample;' -U postgres
    psql -U postgres -d geoexample -c "create extension postgis"
fi

