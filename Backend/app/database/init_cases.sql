INSERT INTO "Cases_DB"."MediaType" (MediaName, MediaExtension) VALUES
('Portable Network Graphics', '.png'),
('Joint Photographic Experts Group', '.jpeg'),
('JPEG Image', '.jpg'),
('Portable Document Format', '.pdf')
ON CONFLICT (MediaName) DO NOTHING;

