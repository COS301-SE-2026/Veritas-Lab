INSERT INTO "Users_DB"."Users" (UserEmail,UserName,UserRole,UserPassword) VALUES
('admin@gmail.com','InvestAdmin','INVESTIGATOR','$2b$12$UOIAVT1LYA8fhv.ynYqbQuXmLs3ZFby6yBLCLHRLmiwxcidpv1tg.')
ON CONFLICT (UserEmail) DO NOTHING;