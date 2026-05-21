INSERT INTO "Users_DB"."Users" (UserEmail,UserName,UserRole,UserPassword) VALUES
('admin@gmail.com','InvestAdmin','INVESTIGATOR','f3ec3f2fecd0464ccd3251d6253a821bf8cffd2e4305f62921ba912883353879')
ON CONFLICT (UserEmail) DO NOTHING;