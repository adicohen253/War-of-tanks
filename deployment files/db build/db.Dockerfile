FROM mysql:8.2
COPY dbsetup.sql ./docker-entrypoint-initdb.d/
