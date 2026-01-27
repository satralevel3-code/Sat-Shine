-- SAT-SHINE PostgreSQL + PostGIS Database Setup
-- Run this script as PostgreSQL superuser

-- Create database
CREATE DATABASE sat_shine_db;

-- Create user
CREATE USER sat_shine_user WITH PASSWORD 'secure_password_123';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE sat_shine_db TO sat_shine_user;
ALTER USER sat_shine_user CREATEDB;

-- Connect to the database
\c sat_shine_db

-- Create PostGIS extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO sat_shine_user;
GRANT CREATE ON SCHEMA public TO sat_shine_user;

-- Verify PostGIS installation
SELECT PostGIS_Version();

-- Show database info
\l+ sat_shine_db