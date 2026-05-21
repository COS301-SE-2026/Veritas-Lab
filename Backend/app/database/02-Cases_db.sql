
Create SCHEMA IF NOT EXISTS "Cases_DB";

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA public;

Create TABLE IF NOT EXISTS "Cases_DB"."MediaType"(
    MediaTypeId UUID PRIMARY KEY DEFAULT public.uuid_generate_v4(),
    MediaName varchar(100) UNIQUE NOT NULL,
    MediaBucket varchar(255) NOT NULL,
    MediaExtension varchar(10) UNIQUE
);

CREATE TABLE IF NOT EXISTS "Cases_DB"."Cases" (
    CaseId UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    CaseReviews JSONB,
    CaseName varchar(255) NOT NULL,
    CaseCreator varchar(100) NOT NULL, -- A case has to have a creator 
    CaseDescription TEXT,
    CaseClosed boolean NOT NULL DEFAULT FALSE,
    CaseCreationDate TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "Cases_DB"."Media"(
    MediaId UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    MediaType UUID NOT NULL REFERENCES "Cases_DB"."MediaType"(MediaTypeId) ON DELETE RESTRICT ON UPDATE CASCADE,
    MediaHash TEXT UNIQUE,
    MediaUploadDate TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "Cases_DB"."Reports"(
    ReportId UUID PRIMARY KEY DEFAULT public.uuid_generate_v4(),
    CaseId UUID NOT NULL REFERENCES "Cases_DB"."Cases"(CaseId) ON DELETE CASCADE ON UPDATE CASCADE,
    ImageId UUID NOT NULL REFERENCES "Cases_DB"."Media"(MediaId) ON UPDATE CASCADE,
    ReportArtifacts JSONB,
    ReportFindings TEXT,
    ReportComments TEXT,
    ReportDateCreation TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);




