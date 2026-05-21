INSERT INTO "Users_DB"."Users" (UserEmail,UserName,UserRole,UserPassword) VALUES
('admin@gmail.com','InvestAdmin','INVESTIGATOR','7efe68ba63fd87f8b53e10800dedf5179cf4897e3fc28a57998bd8f7e3e4e66a')
ON CONFLICT (UserEmail) DO NOTHING;