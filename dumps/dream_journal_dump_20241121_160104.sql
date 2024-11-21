-- Dream Journal Database Dump
-- Created at: 2024-11-21 16:01:05.167001


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
INSERT INTO user (id, username, email, password_hash, subscription_type, subscription_end_date, monthly_ai_analysis_count, last_analysis_reset, is_moderator) VALUES (68, 'user_1', 'user1@example.com', 'scrypt:32768:8:1$WNEO1dnGbOkKCNlD$ffa1bca5f789db2b7fa8a1ff95b0ec98c5aa3600163eab63a4269d1044eabebdeeebc789f543afd3e2ee4ce5228cc3b5c0a583c83e83abaa349c392b94630a3e', 'free', NULL, 3, '2024-11-21 15:59:43.411227', False);
INSERT INTO user (id, username, email, password_hash, subscription_type, subscription_end_date, monthly_ai_analysis_count, last_analysis_reset, is_moderator) VALUES (69, 'user_2', 'user2@example.com', 'scrypt:32768:8:1$B4jGG5bgWDmPdrIW$fc77de9c9d16a3cf21fcb11f94bb864f1e70628fa32b915595d88a1e7dc945109d7ca035ff1a0a5786c73fd9cb2f0c8c8879db12a17d2cf6b7a0b70f975e74b4', 'free', NULL, 0, '2024-11-21 15:59:43.513475', False);
INSERT INTO user (id, username, email, password_hash, subscription_type, subscription_end_date, monthly_ai_analysis_count, last_analysis_reset, is_moderator) VALUES (70, 'user_3', 'user3@example.com', 'scrypt:32768:8:1$TdDXxgGLIdoxrFFE$269aaa7609da371dd4a0e2b5d751a8dfc666e28824ae0b5294709413572e69ecb3d460740411200afa332964b808ac2a884681708bb668f5eede637df8e7509c', 'premium', '2024-12-21 15:59:43.695512', 0, '2024-11-21 15:59:43.608313', False);
INSERT INTO user (id, username, email, password_hash, subscription_type, subscription_end_date, monthly_ai_analysis_count, last_analysis_reset, is_moderator) VALUES (71, 'user_4', 'user4@example.com', 'scrypt:32768:8:1$COs37BmDGm8QsOJu$e2c822d7aec533997e62eff723fabf3600835b09bf761aa805985db60c333382d4da19cb3ce8eacd6fde812923c3243acce5e643495c8e30b4cb754bdca781dc', 'free', NULL, 3, '2024-11-21 15:59:43.695558', False);
INSERT INTO user (id, username, email, password_hash, subscription_type, subscription_end_date, monthly_ai_analysis_count, last_analysis_reset, is_moderator) VALUES (72, 'user_5', 'user5@example.com', 'scrypt:32768:8:1$NGU39YKMKEnLp36E$1614563c7c987c97bbe249ab9e93ed3be4b0145e4beec9a86d017c86baddbe574539cead7b5522e31aff5ca4df66edc25ce91f0eff56fbc6204002b278f6c11d', 'premium', '2024-12-21 15:59:43.859021', 2, '2024-11-21 15:59:43.776352', False);

-- Table: dream
DROP TABLE IF EXISTS dream CASCADE;
CREATE TABLE dream (id integer NOT NULL, user_id integer NOT NULL, title character varying(100) NOT NULL, content text NOT NULL, date timestamp without time zone, mood character varying(50), sentiment_score double precision, sentiment_magnitude double precision, dominant_emotions character varying(200), lucidity_level integer, tags character varying(200), is_public boolean, is_anonymous boolean, ai_analysis text, sleep_duration double precision, sleep_quality integer, bed_time timestamp without time zone, wake_time timestamp without time zone, sleep_interruptions integer, sleep_position character varying(50));

-- Table: comment
DROP TABLE IF EXISTS comment CASCADE;
CREATE TABLE comment (id integer NOT NULL, content text NOT NULL, user_id integer NOT NULL, dream_id integer NOT NULL, created_at timestamp without time zone, edited_at timestamp without time zone, parent_id integer, is_hidden boolean, moderation_reason character varying(200), moderated_at timestamp without time zone, moderated_by integer);

-- Table: group_membership
DROP TABLE IF EXISTS group_membership CASCADE;
CREATE TABLE group_membership (user_id integer NOT NULL, group_id integer NOT NULL, is_admin boolean, joined_at timestamp without time zone);
