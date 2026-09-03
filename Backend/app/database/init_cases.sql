SET app.current_user_id = '00000000-0000-0000-0000-000000000000';

INSERT INTO "Cases_DB"."MediaType" (MediaName,MediaBucket, MediaExtension) VALUES
('Portable Network Graphics','images', '.png'),
('Joint Photographic Experts Group','images', '.jpeg'),
('JPEG Image','images', '.jpg'),
('Portable Document Format','pdf', '.pdf'),
('Multipart version 4','videos', 'mp4')
ON CONFLICT (MediaName) DO NOTHING;

