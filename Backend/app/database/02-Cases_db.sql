
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
    MediaAnnotations JSONB,
    MediaUploadDate TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "Cases_DB"."Reports"(
    ReportId UUID PRIMARY KEY DEFAULT public.uuid_generate_v4(),
    CaseId UUID NOT NULL REFERENCES "Cases_DB"."Cases"(CaseId) ON DELETE CASCADE ON UPDATE CASCADE,
    MediaId UUID NOT NULL REFERENCES "Cases_DB"."Media"(MediaId) ON UPDATE CASCADE,
    ImageTitle Text,
    ReportArtifacts JSONB,
    ReportFindings TEXT,
    ReportComments TEXT,
    ReportCertainty SMALLINT CHECK (ReportCertainty <=3), -- 0=Nothing, 1=low, 2=moderately , 3=high
    ReportDateCreation TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "Cases_DB"."Comments"(
    CommentID BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    CaseId UUID NOT NULL REFERENCES "Cases_DB"."Cases"(CaseId) ON DELETE CASCADE ON UPDATE CASCADE,
    Username varchar(100) NOT NULL,
    Comment TEXT,
    CommentTimestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

create UNIQUE INDEX CaseImage ON "Cases_DB"."Reports"(CaseId, MediaId);

-- Database adjustment scripts start here
ALTER TABLE "Cases_DB"."MediaType" 
ALTER COLUMN MediaExtension SET NOT NULL;


-- BELOW is the Audit tables
CREATE SEQUENCE case_audit_seq START WITH 1 INCREMENT BY 1;

DROP TYPE IF EXISTS queryType CASCADE;
CREATE TYPE queryType AS ENUM ('CREATE','UPDATE','DELETE');

CREATE TABLE IF NOT EXISTS "Cases_DB"."Audit_Cases"(
    audit_case_id int PRIMARY KEY DEFAULT nextval('case_audit_seq'),
    query_executor UUID NOT NULL REFERENCES "Users_DB"."Users"(UserId),
    query_executor_name VARCHAR(100) NOT NULL,
    query_type queryType NOT NULL,
    old_case_id UUID,
    CaseName varchar(255) NOT NULL,
    CaseCreator varchar(100) NOT NULL,
    CaseDescription TEXT,
    CaseClosed boolean NOT NULL DEFAULT FALSE,
    CaseCreationDate TIMESTAMPTZ,
    AuditTimestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);