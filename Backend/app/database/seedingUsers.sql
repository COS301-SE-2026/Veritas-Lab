INSERT INTO "Users_DB"."Users" (UserEmail,UserName,UserRole,UserPassword) VALUES
('admin@gmail.com','InvestAdmin','INVESTIGATOR','835d6dc88b708bc646d6db82c853ef4182fabbd4a8de59c213f2b5ab3ae7d9be')
ON CONFLICT (UserEmail) DO NOTHING;