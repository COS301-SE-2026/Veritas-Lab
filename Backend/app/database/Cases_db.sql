
Create SCHEMA IF NOT EXISTS "Cases_DB";

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA public;

Create TABLE MediaType(
    MediaTypeId UUID PRIMARY KEY DEFAULT public.uuid_generate_v4(),
    MediaName varchar(100) UNIQUE NOT NULL,
    MediaExtension varchar(10) UNIQUE
);

CREATE TABLE Cases (
    CaseId UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    CaseReviews JSONB,
    CaseName varchar(255) NOT NULL,
    CaseCreator varchar(100) NOT NULL, -- A case has to have a creator 
    CaseCreationDate TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Media(
    MediaId UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    MediaType UUID NOT NULL REFERENCES MediaType(MediaTypeId) ON DELETE RESTRICT ON UPDATE CASCADE,
    MediaBucket varchar(255) NOT NULL,
    MediaUploadDate TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Reports(
    ReportId UUID PRIMARY KEY DEFAULT public.uuid_generate_v4(),
    CaseId UUID NOT NULL REFERENCES Cases(CaseId) ON DELETE CASCADE ON UPDATE CASCADE,
    ImageId UUID NOT NULL REFERENCES Media(MediaId) ON UPDATE CASCADE,
    ReportArtifacts JSONB,
    ReportFindings TEXT,
    ReportComments TEXT,
    ReportDateCreation TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);




