-- Dream Journal Database Dump
-- Created at: 2024-11-23 22:18:33.505578


-- Table: notification
DROP TABLE IF EXISTS notification CASCADE;
CREATE TABLE notification (id integer NOT NULL, user_id integer NOT NULL, title character varying(100) NOT NULL, content text NOT NULL, type character varying(50) NOT NULL, reference_id integer, created_at timestamp without time zone, read boolean);
INSERT INTO notification (id, user_id, title, content, type, reference_id, created_at, read) VALUES (1, 1, 'New comment on your dream: Talking to fish', 'Chris commented: this is interesting', 'comment', 2, '2024-11-16 16:55:28.255714', False);
INSERT INTO notification (id, user_id, title, content, type, reference_id, created_at, read) VALUES (2, 1, 'New reply on your dream: Talking to fish', 'Chris replyd: oh wow', 'reply', 2, '2024-11-16 17:21:21.423199', False);
INSERT INTO notification (id, user_id, title, content, type, reference_id, created_at, read) VALUES (3, 1, 'Your comment has been hidden', 'Your comment has been hidden by a moderator. Reason: test', 'moderation', 2, '2024-11-16 17:54:04.729490', False);

-- Table: forum_post
DROP TABLE IF EXISTS forum_post CASCADE;
CREATE TABLE forum_post (id integer NOT NULL, title character varying(200) NOT NULL, content text NOT NULL, user_id integer NOT NULL, group_id integer NOT NULL, created_at timestamp without time zone);

-- Table: forum_reply
DROP TABLE IF EXISTS forum_reply CASCADE;
CREATE TABLE forum_reply (id integer NOT NULL, content text NOT NULL, user_id integer NOT NULL, post_id integer NOT NULL, created_at timestamp without time zone);

-- Table: user_activity
DROP TABLE IF EXISTS user_activity CASCADE;
CREATE TABLE user_activity (id integer NOT NULL, user_id integer NOT NULL, activity_type character varying(50) NOT NULL, description text, target_type character varying(50), target_id integer, created_at timestamp without time zone, ip_address character varying(45), user_agent character varying(256));
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (1, 1, 'login', '{''login_method'': ''password''}', NULL, NULL, '2024-11-16 16:18:20.959246', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (2, 1, 'dream_view', 'Viewed dashboard | {''page'': ''dashboard''}', NULL, NULL, '2024-11-16 16:18:21.220838', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (3, 1, 'dream_view', 'Viewed dashboard | {''page'': ''dashboard''}', NULL, NULL, '2024-11-16 16:19:48.199812', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (4, 1, 'dream_view', 'Viewed dream: Test Dream', NULL, 1, '2024-11-16 16:19:59.109485', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (5, 1, 'login', '{''login_method'': ''password''}', NULL, NULL, '2024-11-16 16:20:41.889689', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (6, 1, 'dream_view', 'Viewed dashboard | {''page'': ''dashboard''}', NULL, NULL, '2024-11-16 16:20:42.187407', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (7, 1, 'dream_view', 'Viewed dream: Test Dream', NULL, 1, '2024-11-16 16:20:50.711133', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (8, 1, 'login', '{''login_method'': ''password''}', NULL, NULL, '2024-11-16 16:23:43.834003', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (9, 1, 'dream_view', 'Viewed dashboard | {''page'': ''dashboard''}', NULL, NULL, '2024-11-16 16:23:44.197236', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (10, 1, 'dream_view', 'Viewed dream: Test Dream', NULL, 1, '2024-11-16 16:23:55.057948', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (11, 1, 'dream_view', 'Viewed dashboard | {''page'': ''dashboard''}', NULL, NULL, '2024-11-16 16:24:00.635650', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (12, 1, 'dream_create', 'Created dream: Talking to fish', NULL, 2, '2024-11-16 16:25:19.797847', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (13, 1, 'dream_view', 'Viewed dream: Talking to fish', NULL, 2, '2024-11-16 16:25:20.180656', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (14, 1, 'dream_patterns_view', 'Viewed dream patterns', NULL, NULL, '2024-11-16 16:25:39.387735', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (15, 1, 'dream_view', 'Viewed dream: Talking to fish', NULL, 2, '2024-11-16 16:25:44.956520', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (16, 1, 'login', '{''login_method'': ''password''}', NULL, NULL, '2024-11-16 16:28:12.345275', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (17, 1, 'dream_view', 'Viewed dashboard | {''page'': ''dashboard''}', NULL, NULL, '2024-11-16 16:28:12.589040', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (18, 1, 'dream_view', 'Viewed dream: Test Dream', NULL, 1, '2024-11-16 16:28:22.192931', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (19, 1, 'dream_view', 'Viewed dashboard | {''page'': ''dashboard''}', NULL, NULL, '2024-11-16 16:28:22.471428', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (20, 1, 'dream_view', 'Viewed dream: Talking to fish', NULL, 2, '2024-11-16 16:28:27.854797', '172.31.196.51', NULL);
INSERT INTO user_activity (id, user_id, activity_type, description, target_type, target_id, created_at, ip_address, user_agent) VALUES (21, 1, 'dream_view', 'Viewed dashboard | {''page'': ''dashboard''}', NULL, NULL, '2024-11-16 16:28:28.170029', '172.31.196.51', NULL);

-- Table: alembic_version
DROP TABLE IF EXISTS alembic_version CASCADE;
CREATE TABLE alembic_version (version_num character varying(32) NOT NULL);
INSERT INTO alembic_version (version_num) VALUES ('77a144934707');

-- Table: dream_group
DROP TABLE IF EXISTS dream_group CASCADE;
CREATE TABLE dream_group (id integer NOT NULL, name character varying(100) NOT NULL, description text, created_by integer NOT NULL, created_at timestamp without time zone);

-- Table: user
DROP TABLE IF EXISTS user CASCADE;
CREATE TABLE user (id integer NOT NULL, username character varying(64) NOT NULL, email character varying(120) NOT NULL, password_hash character varying(256), subscription_type character varying(20), subscription_end_date timestamp without time zone, monthly_ai_analysis_count integer, last_analysis_reset timestamp without time zone, is_moderator boolean);
INSERT INTO user (id, username, email, password_hash, subscription_type, subscription_end_date, monthly_ai_analysis_count, last_analysis_reset, is_moderator) VALUES (74, 'user_1', 'user1@example.com', 'scrypt:32768:8:1$lLOQiL7HfO4l7uSi$e9a81787481156af31778f0bea5875684eba403b70aba2609c9c2f10b2ce2dcf4d380a982109b0768737a874f2abc2ec0c4bf0f2c1df129c014731e0511a96c1', 'free', NULL, 2, '2024-11-23 22:18:28.560970', False);
INSERT INTO user (id, username, email, password_hash, subscription_type, subscription_end_date, monthly_ai_analysis_count, last_analysis_reset, is_moderator) VALUES (75, 'user_2', 'user2@example.com', 'scrypt:32768:8:1$SwhFWWBkQdRzfv60$153ec6f06da9933dbe348312d04a62dca6710fa2309a50145fc653279002a6a85bc74813b260940451f7ecfa16b357703ae4f504b44121b21d708d4b4e31fa58', 'free', NULL, 0, '2024-11-23 22:18:28.650273', False);
INSERT INTO user (id, username, email, password_hash, subscription_type, subscription_end_date, monthly_ai_analysis_count, last_analysis_reset, is_moderator) VALUES (76, 'user_3', 'user3@example.com', 'scrypt:32768:8:1$q0GcFHuclohTf9LZ$248dd72d2f378b32593f7feb8b3e4d39a74bfd79348cd6ce314ad7d85bfc81c76cad9034784fb0dd18cce49f4f02a4e90de6df971e9cce35d5c03abd3c042578', 'premium', '2024-12-23 22:18:28.821526', 3, '2024-11-23 22:18:28.738957', False);
INSERT INTO user (id, username, email, password_hash, subscription_type, subscription_end_date, monthly_ai_analysis_count, last_analysis_reset, is_moderator) VALUES (77, 'user_4', 'user4@example.com', 'scrypt:32768:8:1$BCDgQ8J4teocxMP1$2629b6c45faa5c8c22a9d2ff06afbcdd7ae2433cd1b94a164de74e270c4774fb87f2e1afcd196f4e0a1728baf483eedd8c6878f080b9b75388a791a4eb841a22', 'free', NULL, 0, '2024-11-23 22:18:28.821558', False);
INSERT INTO user (id, username, email, password_hash, subscription_type, subscription_end_date, monthly_ai_analysis_count, last_analysis_reset, is_moderator) VALUES (78, 'user_5', 'user5@example.com', 'scrypt:32768:8:1$ZnJ0Pk5jjCHjroaH$c0d733fdb89c19dfed44112217e01269273287ea2e0933c7907476bb6026a7c77151ecba0f32a1aa687f490650048397dda49ae98c36ca26314e092b6d2d32e1', 'free', NULL, 2, '2024-11-23 22:18:28.910806', False);

-- Table: dream
DROP TABLE IF EXISTS dream CASCADE;
CREATE TABLE dream (id integer NOT NULL, user_id integer NOT NULL, title character varying(100) NOT NULL, content text NOT NULL, date timestamp without time zone, mood character varying(50), sentiment_score double precision, sentiment_magnitude double precision, dominant_emotions character varying(200), lucidity_level integer, tags character varying(200), is_public boolean, is_anonymous boolean, ai_analysis text, sleep_duration double precision, sleep_quality integer, bed_time timestamp without time zone, wake_time timestamp without time zone, sleep_interruptions integer, sleep_position character varying(50));

-- Table: comment
DROP TABLE IF EXISTS comment CASCADE;
CREATE TABLE comment (id integer NOT NULL, content text NOT NULL, user_id integer NOT NULL, dream_id integer NOT NULL, created_at timestamp without time zone, edited_at timestamp without time zone, parent_id integer, is_hidden boolean, moderation_reason character varying(200), moderated_at timestamp without time zone, moderated_by integer);

-- Table: group_membership
DROP TABLE IF EXISTS group_membership CASCADE;
CREATE TABLE group_membership (user_id integer NOT NULL, group_id integer NOT NULL, is_admin boolean, joined_at timestamp without time zone);
