-- Seed cases for development/testing
SET app.current_user_id = '00000000-0000-0000-0000-000000000000';


INSERT INTO "Cases_DB"."Cases" (CaseId, CaseName, CaseCreator, CaseDescription, CaseClosed)
VALUES
    (public.uuid_generate_v4(), 'Burglary at 5th St', 'InvestAdmin', 'Reported break-in and stolen electronics', false),
    (public.uuid_generate_v4(),  'Suspicious activity near mall', 'investigator_amy', 'Multiple witnesses reported someone casing cars', false),
    (public.uuid_generate_v4(),  'Noise complaint escalation', 'INVESTIGATOR', 'Long-running noise complaint, mediation completed', true),
    (public.uuid_generate_v4(),  'Data breach incident', 'INVESTIGATOR', 'Unauthorized access to internal system detected', false),
    (public.uuid_generate_v4(), 'Anonymous tip follow-up', 'investigator_kim', 'Follow-up on anonymous tip; awaiting lab results', false);
