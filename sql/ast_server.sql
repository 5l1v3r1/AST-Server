/*
 Navicat Premium Data Transfer

 Source Server         : Local
 Source Server Type    : MySQL
 Source Server Version : 80017
 Source Host           : localhost:3306
 Source Schema         : ast_server

 Target Server Type    : MySQL
 Target Server Version : 80017
 File Encoding         : 65001

 Date: 14/10/2019 17:58:13
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for users_accounts
-- ----------------------------
DROP TABLE IF EXISTS `users_accounts`;
CREATE TABLE `users_accounts` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user_uuid` varchar(40) DEFAULT NULL,
  `user_first_name` varchar(80) DEFAULT NULL,
  `user_last_name` varchar(80) DEFAULT NULL,
  `user_email` varchar(255) DEFAULT NULL,
  `user_email_status` varchar(20) DEFAULT '0',
  `user_account_status` varchar(20) DEFAULT '0',
  `user_password_hash` varchar(255) DEFAULT NULL,
  `user_account_id` varchar(20) DEFAULT NULL,
  `user_organisation_uuid` varchar(40) DEFAULT NULL,
  `user_organisation_role` varchar(20) DEFAULT NULL,
  `user_permissions_scopes` varchar(500) DEFAULT NULL,
  `created_at` int(10) DEFAULT NULL,
  `deleted_at` int(10) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_email` (`user_email`),
  UNIQUE KEY `user_uuid` (`user_uuid`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8;

-- ----------------------------
-- Table structure for users_diagnostics_headers
-- ----------------------------
DROP TABLE IF EXISTS `users_diagnostics_headers`;
CREATE TABLE `users_diagnostics_headers` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user_uuid` varchar(40) DEFAULT NULL,
  `diagnostic_event_number` varchar(40) DEFAULT NULL,
  `tool_id` varchar(20) DEFAULT NULL,
  `tool_version` varchar(20) DEFAULT NULL,
  `diagnostic_start_timestamp` int(10) DEFAULT NULL,
  `diagnostic_end_timestamp` int(10) DEFAULT NULL,
  `serial_number` varchar(20) DEFAULT NULL,
  `server_id` varchar(20) DEFAULT NULL,
  `account_id` int(10) DEFAULT NULL,
  `profile_file` mediumtext CHARACTER SET latin1 COLLATE latin1_swedish_ci,
  `log_file` mediumtext CHARACTER SET latin1 COLLATE latin1_swedish_ci,
  `test_result` varchar(20) DEFAULT NULL,
  `pass_count` int(10) DEFAULT NULL,
  `created_at` int(10) DEFAULT NULL,
  `deleted_at` int(10) DEFAULT NULL,
  `tech_notes` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `diagnostic_event_number` (`diagnostic_event_number`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for users_diagnostics_results
-- ----------------------------
DROP TABLE IF EXISTS `users_diagnostics_results`;
CREATE TABLE `users_diagnostics_results` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user_uuid` varchar(40) DEFAULT NULL,
  `diagnostic_event_number` varchar(40) DEFAULT NULL,
  `module_name` varchar(100) DEFAULT NULL,
  `module_location` varchar(100) DEFAULT NULL,
  `module_serial_number` varchar(50) DEFAULT NULL,
  `module_test_name` varchar(100) DEFAULT NULL,
  `module_test_number` int(10) DEFAULT NULL,
  `module_test_result` varchar(20) DEFAULT NULL,
  `created_at` int(10) DEFAULT NULL,
  `deleted_at` int(10) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=latin1;

-- ----------------------------
-- Table structure for users_tokens
-- ----------------------------
DROP TABLE IF EXISTS `users_tokens`;
CREATE TABLE `users_tokens` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `user_uuid` varchar(40) DEFAULT NULL,
  `user_session_token` varchar(35) DEFAULT NULL,
  `expires_at` int(10) DEFAULT '0',
  `created_at` int(10) DEFAULT '0',
  `deleted_at` int(10) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_session_token` (`user_session_token`)
) ENGINE=InnoDB AUTO_INCREMENT=7712 DEFAULT CHARSET=utf8;

SET FOREIGN_KEY_CHECKS = 1;
