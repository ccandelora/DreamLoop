-- Dream Journal Database Dump
-- Created at: 2024-11-23 22:19:50.439436


-- Table: notification
DROP TABLE IF EXISTS notification CASCADE;
CREATE TABLE notification (id integer NOT NULL, user_id integer NOT NULL, title character varying(100) NOT NULL, content text NOT NULL, type character varying(50) NOT NULL, reference_id integer, created_at timestamp without time zone, read boolean);
INSERT INTO notification (id, user_id, title, content, type, reference_id, created_at, read) VALUES (1, 1, 'New comment on your dream: Talking to fish', 'Chris commented: this is interesting', 'comment', 2, '2024-11-16 16:55:28.255714', False);
INSERT INTO notification (id, user_id, title, content, type, reference_id, created_at, read) VALUES (2, 1, 'New reply on your dream: Talking to fish', 'Chris replyd: oh wow', 'reply', 2, '2024-11-16 17:21:21.423199', False);
INSERT INTO notification (id, user_id, title, content, type, reference_id, created_at, read) VALUES (3, 1, 'Your comment has been hidden', 'Your comment has been hidden by a moderator. Reason: test', 'moderation', 2, '2024-11-16 17:54:04.729490', False);

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

-- Table: forum_reply
DROP TABLE IF EXISTS forum_reply CASCADE;
CREATE TABLE forum_reply (id integer NOT NULL, content text NOT NULL, user_id integer NOT NULL, post_id integer NOT NULL, created_at timestamp without time zone);

-- Table: forum_post
DROP TABLE IF EXISTS forum_post CASCADE;
CREATE TABLE forum_post (id integer NOT NULL, title character varying(200) NOT NULL, content text NOT NULL, user_id integer NOT NULL, group_id integer NOT NULL, created_at timestamp without time zone);

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
INSERT INTO user (id, username, email, password_hash, subscription_type, subscription_end_date, monthly_ai_analysis_count, last_analysis_reset, is_moderator) VALUES (84, 'user_1', 'user1@example.com', 'scrypt:32768:8:1$ipvDFhcUwH65uYmO$d0ec106aa6126cb15abcec81d05a9edc80cb2fb7695aca310c9a89b6f8dc05284c920c6091248d3ba3e1ec256994c69cf1b21aaf7056eb5e2c9d62b6280635ba', 'free', NULL, 1, '2024-11-23 22:19:44.010020', False);
INSERT INTO user (id, username, email, password_hash, subscription_type, subscription_end_date, monthly_ai_analysis_count, last_analysis_reset, is_moderator) VALUES (85, 'user_2', 'user2@example.com', 'scrypt:32768:8:1$JtgIzdpBcVUelHKO$8cc4106743f8d31a058bf7b75770868763511c693eea0c39a929e01ac334f9ce7b2ccdcca9620bed50cafcbf5c927bd635d1eaa392b59e91c5ff28f1676aa2cc', 'free', NULL, 3, '2024-11-23 22:19:44.117901', False);
INSERT INTO user (id, username, email, password_hash, subscription_type, subscription_end_date, monthly_ai_analysis_count, last_analysis_reset, is_moderator) VALUES (86, 'user_3', 'user3@example.com', 'scrypt:32768:8:1$zvEkMqYhvsgP6Kxk$8bcbe1d789ace2a51d83fa07d85e98a36fe3f08b37c49681d20af8157072489a17938277cc97527ec40f03c385a50cd6ae3d8ec14d8c0656808c8aa2e2c218de', 'premium', '2024-12-23 22:19:44.361397', 3, '2024-11-23 22:19:44.235136', False);
INSERT INTO user (id, username, email, password_hash, subscription_type, subscription_end_date, monthly_ai_analysis_count, last_analysis_reset, is_moderator) VALUES (87, 'user_4', 'user4@example.com', 'scrypt:32768:8:1$zf02FOFdXtKx72og$19930130ba5a7593d28b06d2888ebe89c05e050bdb25bca3d1710bc72ae161a29e3bdaf8b6a10b5c5874645c431c3066ffbf78e777eaaed7ba6134ff89a9d07d', 'free', NULL, 0, '2024-11-23 22:19:44.361439', False);
INSERT INTO user (id, username, email, password_hash, subscription_type, subscription_end_date, monthly_ai_analysis_count, last_analysis_reset, is_moderator) VALUES (88, 'user_5', 'user5@example.com', 'scrypt:32768:8:1$vrcigsdVA9VRSLy1$1e2da9afb55c162b61908343c344578a819cd35c2b78e9a4e48c8fd1b18fa9e31b07a20bd4c03aeda81a0747f3f3f449b0ab135f98445080b3e53bc55aabf371', 'premium', '2024-12-23 22:19:44.583737', 0, '2024-11-23 22:19:44.472789', False);

-- Table: dream
DROP TABLE IF EXISTS dream CASCADE;
CREATE TABLE dream (id integer NOT NULL, user_id integer NOT NULL, title character varying(100) NOT NULL, content text NOT NULL, date timestamp without time zone, mood character varying(50), sentiment_score double precision, sentiment_magnitude double precision, dominant_emotions character varying(200), lucidity_level integer, tags character varying(200), is_public boolean, is_anonymous boolean, ai_analysis text, sleep_duration double precision, sleep_quality integer, bed_time timestamp without time zone, wake_time timestamp without time zone, sleep_interruptions integer, sleep_position character varying(50));

-- Table: comment
DROP TABLE IF EXISTS comment CASCADE;
CREATE TABLE comment (id integer NOT NULL, content text NOT NULL, user_id integer NOT NULL, dream_id integer NOT NULL, created_at timestamp without time zone, edited_at timestamp without time zone, parent_id integer, is_hidden boolean, moderation_reason character varying(200), moderated_at timestamp without time zone, moderated_by integer);

-- Table: group_membership
DROP TABLE IF EXISTS group_membership CASCADE;
CREATE TABLE group_membership (user_id integer NOT NULL, group_id integer NOT NULL, is_admin boolean, joined_at timestamp without time zone);
