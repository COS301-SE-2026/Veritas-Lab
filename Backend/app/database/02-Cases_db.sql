
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
CREATE TYPE queryType AS ENUM ('INSERT','UPDATE','DELETE');

CREATE TABLE IF NOT EXISTS "Cases_DB"."Audit_Cases"(
    audit_case_id int PRIMARY KEY DEFAULT nextval('case_audit_seq'),
    query_executor UUID NOT NULL REFERENCES "Users_DB"."Users"(UserId),
    query_executor_name VARCHAR(100) NOT NULL,
    query_type queryType NOT NULL,
    old_case_id UUID,
    old_CaseName varchar(255) NOT NULL,
    old_CaseCreator varchar(100) NOT NULL,
    old_CaseDescription TEXT,
    old_CaseClosed boolean NOT NULL DEFAULT FALSE,
    old_CaseCreationDate TIMESTAMPTZ,
    AuditTimestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE IF NOT EXISTS mediatype_audit_seq START WITH 1 INCREMENT BY 1;

CREATE TABLE IF NOT EXISTS "Cases_DB"."Audit_MediaTypes"(
    audit_mediatype_id int PRIMARY KEY DEFAULT nextval('mediatype_audit_seq'),
    query_executor UUID NOT NULL REFERENCES "Users_DB"."Users"(UserId),
    query_executor_name VARCHAR(100) NOT NULL,
    query_type queryType NOT NULL,
    old_mediatype_id UUID,
    old_MediaName varchar(100) NOT NULL,
    old_MediaBucket varchar(255) NOT NULL,
    old_MediaExtension varchar(10) NOT NULL,
    AuditTimestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE IF NOT EXISTS media_audit_seq START WITH 1 INCREMENT BY 1;

CREATE TABLE IF NOT EXISTS "Cases_DB"."Audit_Media"(
    audit_media_id int PRIMARY KEY DEFAULT nextval('media_audit_seq'),
    query_executor UUID NOT NULL REFERENCES "Users_DB"."Users"(UserId),
    query_executor_name VARCHAR(100) NOT NULL,
    query_type queryType NOT NULL,
    old_media_id UUID,
    old_MediaType UUID,
    old_MediaHash TEXT,
    old_MediaAnnotations JSONB,
    old_MediaUploadDate TIMESTAMPTZ,
    AuditTimestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE SEQUENCE IF NOT EXISTS comment_audit_seq START WITH 1 INCREMENT BY 1;

CREATE TABLE IF NOT EXISTS "Cases_DB"."Audit_Comments"(
    audit_comment_id int PRIMARY KEY DEFAULT nextval('comment_audit_seq'),
    query_executor UUID NOT NULL REFERENCES "Users_DB"."Users"(UserId),
    query_executor_name VARCHAR(100) NOT NULL,
    query_type queryType NOT NULL,
    old_comment_id BIGINT,
    old_CaseId UUID,
    old_Username varchar(100),
    old_Comment TEXT,
    old_CommentTimestamp TIMESTAMPTZ,
    AuditTimestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION "Cases_DB".get_audit_executor(
    OUT executor_id UUID, 
    OUT executor_name VARCHAR(100)
) AS $$
DECLARE
    v_user_setting TEXT;
BEGIN
    v_user_setting := NULLIF(current_setting('app.current_user_id', true), '');
    IF v_user_setting IS NULL THEN
        RAISE EXCEPTION 'Audit constraint failure: Session variable "app.current_user_id" is not set.';
    END IF;

    executor_id := v_user_setting::UUID;
    SELECT UserName INTO executor_name
    FROM "Users_DB"."Users"
    WHERE UserId = executor_id;

    IF executor_name IS NULL THEN
        RAISE EXCEPTION 'This user is unauthorised to preform this task', executor_id;
    END IF;

END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION "Cases_DB".audit_mediatypes_delete_trigger()
RETURNS TRIGGER AS $$
DECLARE
    v_executor_id UUID;
    v_executor_name VARCHAR(100);
BEGIN
    SELECT executor_id, executor_name INTO v_executor_id, v_executor_name 
    FROM "Cases_DB".get_audit_executor();

    INSERT INTO "Cases_DB"."Audit_MediaTypes" (
        query_executor, query_executor_name, query_type,
        old_mediatype_id, old_MediaName, old_MediaBucket, old_MediaExtension
    ) VALUES (
        v_executor_id, v_executor_name, 'DELETE'::queryType,
        OLD.MediaTypeId, OLD.MediaName, OLD.MediaBucket, OLD.MediaExtension
    );
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_audit_mediatypes_delete
AFTER DELETE ON "Cases_DB"."MediaType"
FOR EACH ROW EXECUTE FUNCTION "Cases_DB".audit_mediatypes_delete_trigger();

CREATE OR REPLACE FUNCTION "Cases_DB".audit_mediatypes_table_modify()
RETURNS TRIGGER AS $$
DECLARE
    v_executor_id UUID;
    v_executor_name VARCHAR(100);
BEGIN
    SELECT executor_id, executor_name INTO v_executor_id, v_executor_name 
    FROM "Cases_DB".get_audit_executor();

    IF TG_OP = 'INSERT' THEN
        INSERT INTO "Cases_DB"."Audit_MediaTypes" (
            query_executor, query_executor_name, query_type,
            old_mediatype_id, old_MediaName, old_MediaBucket, old_MediaExtension
        ) VALUES (
            v_executor_id, v_executor_name, 'INSERT'::queryType,
            NEW.MediaTypeId, NEW.MediaName, NEW.MediaBucket, NEW.MediaExtension
        );
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO "Cases_DB"."Audit_MediaTypes" (
            query_executor, query_executor_name, query_type,
            old_mediatype_id, old_MediaName, old_MediaBucket, old_MediaExtension
        ) VALUES (
            v_executor_id, v_executor_name, 'UPDATE'::queryType,
            OLD.MediaTypeId, OLD.MediaName, OLD.MediaBucket, OLD.MediaExtension
        );
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER audit_mediatypes_modify_trigger
AFTER INSERT OR UPDATE ON "Cases_DB"."MediaType"
FOR EACH ROW EXECUTE FUNCTION "Cases_DB".audit_mediatypes_table_modify();

CREATE OR REPLACE FUNCTION "Cases_DB".audit_media_delete()
RETURNS TRIGGER AS $$
DECLARE
    v_executor_id UUID;
    v_executor_name VARCHAR(100);
BEGIN
    SELECT executor_id, executor_name INTO v_executor_id, v_executor_name 
    FROM "Cases_DB".get_audit_executor();

    INSERT INTO "Cases_DB"."Audit_Media" (
        query_executor, query_executor_name, query_type,
        old_media_id, old_MediaType, old_MediaHash, old_MediaAnnotations, old_MediaUploadDate
    ) VALUES (
        v_executor_id, v_executor_name, 'DELETE'::queryType,
        OLD.MediaId, OLD.MediaType, OLD.MediaHash, OLD.MediaAnnotations, OLD.MediaUploadDate
    );
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER audit_media_delete_trigger
AFTER DELETE ON "Cases_DB"."Media"
FOR EACH ROW EXECUTE FUNCTION "Cases_DB".audit_media_delete();