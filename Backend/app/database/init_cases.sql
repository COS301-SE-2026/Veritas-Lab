INSERT INTO "Cases_DB"."MediaType" (MediaName,MediaBucket, MediaExtension) VALUES
('Portable Network Graphics','images', '.png'),
('Joint Photographic Experts Group','images' '.jpeg'),
('JPEG Image','images', '.jpg'),
('Portable Document Format','pdf', '.pdf')
ON CONFLICT (MediaName) DO NOTHING;

