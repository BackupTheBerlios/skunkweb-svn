#! /bin/bash

dropdb -Upydotest pydotest
dropuser -Upostgres pydotest
createuser -A -d -Upostgres pydotest
createdb -Upydotest pydotest
psql -Upydotest -dpydotest < postgres.sql