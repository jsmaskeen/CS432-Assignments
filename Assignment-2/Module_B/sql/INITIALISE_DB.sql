CREATE DATABASE  IF NOT EXISTS `cabSharing` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `cabSharing`;
-- MySQL dump 10.13  Distrib 8.0.36, for Linux (x86_64)
--
-- Host: localhost    Database: cabSharing
-- ------------------------------------------------------
-- Server version	8.0.45-0ubuntu0.24.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `Bookings`
--

DROP TABLE IF EXISTS `Bookings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Bookings` (
  `BookingID` int NOT NULL AUTO_INCREMENT,
  `RideID` int NOT NULL,
  `Passenger_MemberID` int NOT NULL,
  `Booking_Status` enum('Pending','Confirmed','Rejected','Cancelled') NOT NULL DEFAULT 'Pending',
  `Pickup_GeoHash` varchar(20) NOT NULL,
  `Drop_GeoHash` varchar(20) NOT NULL,
  `Distance_Travelled_KM` decimal(6,2) NOT NULL,
  `Booked_At` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`BookingID`),
  UNIQUE KEY `RideID` (`RideID`,`Passenger_MemberID`),
  KEY `Passenger_MemberID` (`Passenger_MemberID`),
  CONSTRAINT `Bookings_ibfk_1` FOREIGN KEY (`RideID`) REFERENCES `Rides` (`RideID`) ON DELETE CASCADE,
  CONSTRAINT `Bookings_ibfk_2` FOREIGN KEY (`Passenger_MemberID`) REFERENCES `Members` (`MemberID`) ON DELETE CASCADE,
  CONSTRAINT `Bookings_chk_1` CHECK ((`Distance_Travelled_KM` > 0))
) ENGINE=InnoDB AUTO_INCREMENT=54 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `Cost_Settlements`
--

DROP TABLE IF EXISTS `Cost_Settlements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Cost_Settlements` (
  `SettlementID` int NOT NULL AUTO_INCREMENT,
  `BookingID` int NOT NULL,
  `Calculated_Cost` decimal(8,2) NOT NULL,
  `Payment_Status` enum('Unpaid','Settled') NOT NULL DEFAULT 'Unpaid',
  PRIMARY KEY (`SettlementID`),
  UNIQUE KEY `BookingID` (`BookingID`),
  CONSTRAINT `Cost_Settlements_ibfk_1` FOREIGN KEY (`BookingID`) REFERENCES `Bookings` (`BookingID`) ON DELETE CASCADE,
  CONSTRAINT `Cost_Settlements_chk_1` CHECK ((`Calculated_Cost` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=54 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `Locations`
--

DROP TABLE IF EXISTS `Locations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Locations` (
  `LocationID` int NOT NULL AUTO_INCREMENT,
  `Location_Name` varchar(100) NOT NULL,
  `Location_Type` varchar(20) NOT NULL,
  `GeoHash` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`LocationID`),
  UNIQUE KEY `Location_Name` (`Location_Name`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `Members`
--

DROP TABLE IF EXISTS `Members`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Members` (
  `MemberID` int NOT NULL AUTO_INCREMENT,
  `OAUTH_TOKEN` varchar(100) NOT NULL,
  `Email` varchar(100) NOT NULL,
  `Full_Name` varchar(100) NOT NULL,
  `Reputation_Score` decimal(2,1) NOT NULL DEFAULT '0.0',
  `Phone_Number` varchar(15) DEFAULT NULL,
  `Created_At` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Gender` enum('Male','Female','Other') NOT NULL,
  PRIMARY KEY (`MemberID`),
  UNIQUE KEY `OAUTH_TOKEN` (`OAUTH_TOKEN`),
  UNIQUE KEY `Email` (`Email`),
  CONSTRAINT `Members_chk_1` CHECK ((`Email` like _utf8mb4'%@iitgn.ac.in')),
  CONSTRAINT `Members_chk_2` CHECK ((`Reputation_Score` between 0.0 and 5.0))
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `Reputation_Reviews`
--

DROP TABLE IF EXISTS `Reputation_Reviews`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Reputation_Reviews` (
  `ReviewID` int NOT NULL AUTO_INCREMENT,
  `RideID` int NOT NULL,
  `Reviewer_MemberID` int NOT NULL,
  `Reviewee_MemberID` int NOT NULL,
  `Rating` int NOT NULL,
  `Comments` text,
  `Created_At` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ReviewID`),
  UNIQUE KEY `RideID` (`RideID`,`Reviewer_MemberID`,`Reviewee_MemberID`),
  KEY `Reviewer_MemberID` (`Reviewer_MemberID`),
  KEY `Reviewee_MemberID` (`Reviewee_MemberID`),
  CONSTRAINT `Reputation_Reviews_ibfk_1` FOREIGN KEY (`RideID`) REFERENCES `Rides` (`RideID`) ON DELETE CASCADE,
  CONSTRAINT `Reputation_Reviews_ibfk_2` FOREIGN KEY (`Reviewer_MemberID`) REFERENCES `Members` (`MemberID`) ON DELETE CASCADE,
  CONSTRAINT `Reputation_Reviews_ibfk_3` FOREIGN KEY (`Reviewee_MemberID`) REFERENCES `Members` (`MemberID`) ON DELETE CASCADE,
  CONSTRAINT `Reputation_Reviews_chk_1` CHECK ((`Rating` between 1 and 5)),
  CONSTRAINT `Reputation_Reviews_chk_2` CHECK ((`Reviewer_MemberID` <> `Reviewee_MemberID`))
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `Ride_Chat`
--

DROP TABLE IF EXISTS `Ride_Chat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Ride_Chat` (
  `MessageID` int NOT NULL AUTO_INCREMENT,
  `RideID` int NOT NULL,
  `Sender_MemberID` int NOT NULL,
  `Message_Body` text NOT NULL,
  `Sent_At` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`MessageID`),
  KEY `RideID` (`RideID`),
  KEY `Sender_MemberID` (`Sender_MemberID`),
  CONSTRAINT `Ride_Chat_ibfk_1` FOREIGN KEY (`RideID`) REFERENCES `Rides` (`RideID`) ON DELETE CASCADE,
  CONSTRAINT `Ride_Chat_ibfk_2` FOREIGN KEY (`Sender_MemberID`) REFERENCES `Members` (`MemberID`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `Ride_Participants`
--

DROP TABLE IF EXISTS `Ride_Participants`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Ride_Participants` (
  `ParticipantID` int NOT NULL AUTO_INCREMENT,
  `RideID` int NOT NULL,
  `MemberID` int NOT NULL,
  `Role` enum('Host','Passenger') NOT NULL,
  `Joined_At` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`ParticipantID`),
  UNIQUE KEY `RideID` (`RideID`,`MemberID`),
  KEY `MemberID` (`MemberID`),
  CONSTRAINT `Ride_Participants_ibfk_1` FOREIGN KEY (`RideID`) REFERENCES `Rides` (`RideID`) ON DELETE CASCADE,
  CONSTRAINT `Ride_Participants_ibfk_2` FOREIGN KEY (`MemberID`) REFERENCES `Members` (`MemberID`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=79 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `Rides`
--

DROP TABLE IF EXISTS `Rides`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Rides` (
  `RideID` int NOT NULL AUTO_INCREMENT,
  `Host_MemberID` int NOT NULL,
  `Start_GeoHash` varchar(20) NOT NULL,
  `End_GeoHash` varchar(20) NOT NULL,
  `Departure_Time` datetime NOT NULL,
  `Vehicle_Type` varchar(50) NOT NULL,
  `Max_Capacity` int NOT NULL,
  `Available_Seats` int NOT NULL,
  `Base_Fare_Per_KM` decimal(8,2) NOT NULL,
  `Ride_Status` enum('Open','Started','Full','Cancelled','Completed') NOT NULL DEFAULT 'Open',
  `Created_At` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`RideID`),
  KEY `Host_MemberID` (`Host_MemberID`),
  CONSTRAINT `Rides_ibfk_1` FOREIGN KEY (`Host_MemberID`) REFERENCES `Members` (`MemberID`),
  CONSTRAINT `Rides_chk_1` CHECK ((`Max_Capacity` > 0)),
  CONSTRAINT `Rides_chk_2` CHECK ((`Available_Seats` >= 0)),
  CONSTRAINT `Rides_chk_3` CHECK ((`Available_Seats` <= `Max_Capacity`)),
  CONSTRAINT `Rides_chk_4` CHECK ((`Start_GeoHash` <> `End_GeoHash`))
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `Saved_Addresses`
--

DROP TABLE IF EXISTS `Saved_Addresses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `Saved_Addresses` (
  `AddressID` int NOT NULL AUTO_INCREMENT,
  `MemberID` int NOT NULL,
  `Label` varchar(50) NOT NULL,
  `LocationID` int NOT NULL,
  PRIMARY KEY (`AddressID`),
  KEY `LocationID` (`LocationID`),
  KEY `MemberID` (`MemberID`),
  CONSTRAINT `Saved_Addresses_ibfk_1` FOREIGN KEY (`LocationID`) REFERENCES `Locations` (`LocationID`) ON DELETE CASCADE,
  CONSTRAINT `Saved_Addresses_ibfk_2` FOREIGN KEY (`MemberID`) REFERENCES `Members` (`MemberID`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `User_Preferences`
--

DROP TABLE IF EXISTS `User_Preferences`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `User_Preferences` (
  `PreferenceID` int NOT NULL AUTO_INCREMENT,
  `MemberID` int NOT NULL,
  `Gender_Preference` enum('Any','Same-Gender Only') NOT NULL,
  `Notify_On_New_Ride` tinyint(1) NOT NULL DEFAULT '0',
  `Music_Preference` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`PreferenceID`),
  UNIQUE KEY `MemberID` (`MemberID`),
  CONSTRAINT `User_Preferences_ibfk_1` FOREIGN KEY (`MemberID`) REFERENCES `Members` (`MemberID`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


-- 
-- Triggers for audit logging and unauthorized change detection
--

CREATE TABLE IF NOT EXISTS audit_modification_log (
  log_id BIGINT NOT NULL AUTO_INCREMENT,
  table_name VARCHAR(64) NOT NULL,
  operation ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
  primary_key_name VARCHAR(64) NOT NULL,
  primary_key_value VARCHAR(255) NOT NULL,
  old_values_json JSON NULL,
  new_values_json JSON NULL,
  db_user VARCHAR(128) NOT NULL,
  connection_id BIGINT NOT NULL,
  app_request_id VARCHAR(64) NULL,
  app_actor_member_id INT NULL,
  app_actor_username VARCHAR(100) NULL,
  app_actor_role VARCHAR(20) NULL,
  source_tag VARCHAR(20) NOT NULL,
  is_authorized TINYINT(1) NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (log_id),
  KEY idx_audit_created_at (created_at),
  KEY idx_audit_authorized (is_authorized),
  KEY idx_audit_table_op (table_name, operation)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

DROP VIEW IF EXISTS unauthorized_modifications_view;
CREATE VIEW unauthorized_modifications_view AS
SELECT
  log_id,
  table_name,
  operation,
  primary_key_name,
  primary_key_value,
  db_user,
  connection_id,
  source_tag,
  is_authorized,
  created_at,
  old_values_json,
  new_values_json
FROM audit_modification_log
WHERE is_authorized = 0
ORDER BY log_id DESC;

DELIMITER $$

DROP TRIGGER IF EXISTS trg_rides_ai $$
CREATE TRIGGER trg_rides_ai
AFTER INSERT ON Rides
FOR EACH ROW
BEGIN
  INSERT INTO audit_modification_log (
    table_name, operation, primary_key_name, primary_key_value,
    old_values_json, new_values_json,
    db_user, connection_id,
    app_request_id, app_actor_member_id, app_actor_username, app_actor_role,
    source_tag, is_authorized
  ) VALUES (
    'Rides', 'INSERT', 'RideID', CAST(NEW.RideID AS CHAR),
    NULL,
    JSON_OBJECT(
      'RideID', NEW.RideID,
      'Host_MemberID', NEW.Host_MemberID,
      'Start_GeoHash', NEW.Start_GeoHash,
      'End_GeoHash', NEW.End_GeoHash,
      'Departure_Time', NEW.Departure_Time,
      'Ride_Status', NEW.Ride_Status,
      'Available_Seats', NEW.Available_Seats
    ),
    CURRENT_USER(), CONNECTION_ID(),
    @app_request_id, @app_actor_member_id, @app_actor_username, @app_actor_role,
    IF(COALESCE(@app_source, '') = 'api', 'api', 'direct_db'),
    IF(COALESCE(@app_source, '') = 'api', 1, 0)
  );
END $$

DROP TRIGGER IF EXISTS trg_rides_au $$
CREATE TRIGGER trg_rides_au
AFTER UPDATE ON Rides
FOR EACH ROW
BEGIN
  INSERT INTO audit_modification_log (
    table_name, operation, primary_key_name, primary_key_value,
    old_values_json, new_values_json,
    db_user, connection_id,
    app_request_id, app_actor_member_id, app_actor_username, app_actor_role,
    source_tag, is_authorized
  ) VALUES (
    'Rides', 'UPDATE', 'RideID', CAST(NEW.RideID AS CHAR),
    JSON_OBJECT(
      'Ride_Status', OLD.Ride_Status,
      'Available_Seats', OLD.Available_Seats,
      'Max_Capacity', OLD.Max_Capacity,
      'Base_Fare_Per_KM', OLD.Base_Fare_Per_KM
    ),
    JSON_OBJECT(
      'Ride_Status', NEW.Ride_Status,
      'Available_Seats', NEW.Available_Seats,
      'Max_Capacity', NEW.Max_Capacity,
      'Base_Fare_Per_KM', NEW.Base_Fare_Per_KM
    ),
    CURRENT_USER(), CONNECTION_ID(),
    @app_request_id, @app_actor_member_id, @app_actor_username, @app_actor_role,
    IF(COALESCE(@app_source, '') = 'api', 'api', 'direct_db'),
    IF(COALESCE(@app_source, '') = 'api', 1, 0)
  );
END $$

DROP TRIGGER IF EXISTS trg_rides_ad $$
CREATE TRIGGER trg_rides_ad
AFTER DELETE ON Rides
FOR EACH ROW
BEGIN
  INSERT INTO audit_modification_log (
    table_name, operation, primary_key_name, primary_key_value,
    old_values_json, new_values_json,
    db_user, connection_id,
    app_request_id, app_actor_member_id, app_actor_username, app_actor_role,
    source_tag, is_authorized
  ) VALUES (
    'Rides', 'DELETE', 'RideID', CAST(OLD.RideID AS CHAR),
    JSON_OBJECT(
      'RideID', OLD.RideID,
      'Host_MemberID', OLD.Host_MemberID,
      'Ride_Status', OLD.Ride_Status
    ),
    NULL,
    CURRENT_USER(), CONNECTION_ID(),
    @app_request_id, @app_actor_member_id, @app_actor_username, @app_actor_role,
    IF(COALESCE(@app_source, '') = 'api', 'api', 'direct_db'),
    IF(COALESCE(@app_source, '') = 'api', 1, 0)
  );
END $$

DROP TRIGGER IF EXISTS trg_bookings_ai $$
CREATE TRIGGER trg_bookings_ai
AFTER INSERT ON Bookings
FOR EACH ROW
BEGIN
  INSERT INTO audit_modification_log (
    table_name, operation, primary_key_name, primary_key_value,
    old_values_json, new_values_json,
    db_user, connection_id,
    app_request_id, app_actor_member_id, app_actor_username, app_actor_role,
    source_tag, is_authorized
  ) VALUES (
    'Bookings', 'INSERT', 'BookingID', CAST(NEW.BookingID AS CHAR),
    NULL,
    JSON_OBJECT(
      'BookingID', NEW.BookingID,
      'RideID', NEW.RideID,
      'Passenger_MemberID', NEW.Passenger_MemberID,
      'Booking_Status', NEW.Booking_Status,
      'Distance_Travelled_KM', NEW.Distance_Travelled_KM
    ),
    CURRENT_USER(), CONNECTION_ID(),
    @app_request_id, @app_actor_member_id, @app_actor_username, @app_actor_role,
    IF(COALESCE(@app_source, '') = 'api', 'api', 'direct_db'),
    IF(COALESCE(@app_source, '') = 'api', 1, 0)
  );
END $$

DROP TRIGGER IF EXISTS trg_bookings_au $$
CREATE TRIGGER trg_bookings_au
AFTER UPDATE ON Bookings
FOR EACH ROW
BEGIN
  INSERT INTO audit_modification_log (
    table_name, operation, primary_key_name, primary_key_value,
    old_values_json, new_values_json,
    db_user, connection_id,
    app_request_id, app_actor_member_id, app_actor_username, app_actor_role,
    source_tag, is_authorized
  ) VALUES (
    'Bookings', 'UPDATE', 'BookingID', CAST(NEW.BookingID AS CHAR),
    JSON_OBJECT(
      'Booking_Status', OLD.Booking_Status,
      'Distance_Travelled_KM', OLD.Distance_Travelled_KM
    ),
    JSON_OBJECT(
      'Booking_Status', NEW.Booking_Status,
      'Distance_Travelled_KM', NEW.Distance_Travelled_KM
    ),
    CURRENT_USER(), CONNECTION_ID(),
    @app_request_id, @app_actor_member_id, @app_actor_username, @app_actor_role,
    IF(COALESCE(@app_source, '') = 'api', 'api', 'direct_db'),
    IF(COALESCE(@app_source, '') = 'api', 1, 0)
  );
END $$

DROP TRIGGER IF EXISTS trg_bookings_ad $$
CREATE TRIGGER trg_bookings_ad
AFTER DELETE ON Bookings
FOR EACH ROW
BEGIN
  INSERT INTO audit_modification_log (
    table_name, operation, primary_key_name, primary_key_value,
    old_values_json, new_values_json,
    db_user, connection_id,
    app_request_id, app_actor_member_id, app_actor_username, app_actor_role,
    source_tag, is_authorized
  ) VALUES (
    'Bookings', 'DELETE', 'BookingID', CAST(OLD.BookingID AS CHAR),
    JSON_OBJECT(
      'BookingID', OLD.BookingID,
      'RideID', OLD.RideID,
      'Passenger_MemberID', OLD.Passenger_MemberID,
      'Booking_Status', OLD.Booking_Status
    ),
    NULL,
    CURRENT_USER(), CONNECTION_ID(),
    @app_request_id, @app_actor_member_id, @app_actor_username, @app_actor_role,
    IF(COALESCE(@app_source, '') = 'api', 'api', 'direct_db'),
    IF(COALESCE(@app_source, '') = 'api', 1, 0)
  );
END $$

DROP TRIGGER IF EXISTS trg_settlements_ai $$
CREATE TRIGGER trg_settlements_ai
AFTER INSERT ON Cost_Settlements
FOR EACH ROW
BEGIN
  INSERT INTO audit_modification_log (
    table_name, operation, primary_key_name, primary_key_value,
    old_values_json, new_values_json,
    db_user, connection_id,
    app_request_id, app_actor_member_id, app_actor_username, app_actor_role,
    source_tag, is_authorized
  ) VALUES (
    'Cost_Settlements', 'INSERT', 'SettlementID', CAST(NEW.SettlementID AS CHAR),
    NULL,
    JSON_OBJECT(
      'SettlementID', NEW.SettlementID,
      'BookingID', NEW.BookingID,
      'Calculated_Cost', NEW.Calculated_Cost,
      'Payment_Status', NEW.Payment_Status
    ),
    CURRENT_USER(), CONNECTION_ID(),
    @app_request_id, @app_actor_member_id, @app_actor_username, @app_actor_role,
    IF(COALESCE(@app_source, '') = 'api', 'api', 'direct_db'),
    IF(COALESCE(@app_source, '') = 'api', 1, 0)
  );
END $$

DROP TRIGGER IF EXISTS trg_settlements_au $$
CREATE TRIGGER trg_settlements_au
AFTER UPDATE ON Cost_Settlements
FOR EACH ROW
BEGIN
  INSERT INTO audit_modification_log (
    table_name, operation, primary_key_name, primary_key_value,
    old_values_json, new_values_json,
    db_user, connection_id,
    app_request_id, app_actor_member_id, app_actor_username, app_actor_role,
    source_tag, is_authorized
  ) VALUES (
    'Cost_Settlements', 'UPDATE', 'SettlementID', CAST(NEW.SettlementID AS CHAR),
    JSON_OBJECT(
      'Calculated_Cost', OLD.Calculated_Cost,
      'Payment_Status', OLD.Payment_Status
    ),
    JSON_OBJECT(
      'Calculated_Cost', NEW.Calculated_Cost,
      'Payment_Status', NEW.Payment_Status
    ),
    CURRENT_USER(), CONNECTION_ID(),
    @app_request_id, @app_actor_member_id, @app_actor_username, @app_actor_role,
    IF(COALESCE(@app_source, '') = 'api', 'api', 'direct_db'),
    IF(COALESCE(@app_source, '') = 'api', 1, 0)
  );
END $$

DROP TRIGGER IF EXISTS trg_settlements_ad $$
CREATE TRIGGER trg_settlements_ad
AFTER DELETE ON Cost_Settlements
FOR EACH ROW
BEGIN
  INSERT INTO audit_modification_log (
    table_name, operation, primary_key_name, primary_key_value,
    old_values_json, new_values_json,
    db_user, connection_id,
    app_request_id, app_actor_member_id, app_actor_username, app_actor_role,
    source_tag, is_authorized
  ) VALUES (
    'Cost_Settlements', 'DELETE', 'SettlementID', CAST(OLD.SettlementID AS CHAR),
    JSON_OBJECT(
      'SettlementID', OLD.SettlementID,
      'BookingID', OLD.BookingID,
      'Payment_Status', OLD.Payment_Status
    ),
    NULL,
    CURRENT_USER(), CONNECTION_ID(),
    @app_request_id, @app_actor_member_id, @app_actor_username, @app_actor_role,
    IF(COALESCE(@app_source, '') = 'api', 'api', 'direct_db'),
    IF(COALESCE(@app_source, '') = 'api', 1, 0)
  );
END $$

DROP TRIGGER IF EXISTS trg_members_au $$
CREATE TRIGGER trg_members_au
AFTER UPDATE ON Members
FOR EACH ROW
BEGIN
  INSERT INTO audit_modification_log (
    table_name, operation, primary_key_name, primary_key_value,
    old_values_json, new_values_json,
    db_user, connection_id,
    app_request_id, app_actor_member_id, app_actor_username, app_actor_role,
    source_tag, is_authorized
  ) VALUES (
    'Members', 'UPDATE', 'MemberID', CAST(NEW.MemberID AS CHAR),
    JSON_OBJECT(
      'Email', OLD.Email,
      'Full_Name', OLD.Full_Name,
      'Reputation_Score', OLD.Reputation_Score
    ),
    JSON_OBJECT(
      'Email', NEW.Email,
      'Full_Name', NEW.Full_Name,
      'Reputation_Score', NEW.Reputation_Score
    ),
    CURRENT_USER(), CONNECTION_ID(),
    @app_request_id, @app_actor_member_id, @app_actor_username, @app_actor_role,
    IF(COALESCE(@app_source, '') = 'api', 'api', 'direct_db'),
    IF(COALESCE(@app_source, '') = 'api', 1, 0)
  );
END $$

DROP TRIGGER IF EXISTS trg_auth_credentials_au $$
CREATE TRIGGER trg_auth_credentials_au
AFTER UPDATE ON Auth_Credentials
FOR EACH ROW
BEGIN
  INSERT INTO audit_modification_log (
    table_name, operation, primary_key_name, primary_key_value,
    old_values_json, new_values_json,
    db_user, connection_id,
    app_request_id, app_actor_member_id, app_actor_username, app_actor_role,
    source_tag, is_authorized
  ) VALUES (
    'Auth_Credentials', 'UPDATE', 'CredentialID', CAST(NEW.CredentialID AS CHAR),
    JSON_OBJECT(
      'Username', OLD.Username,
      'Role', OLD.Role
    ),
    JSON_OBJECT(
      'Username', NEW.Username,
      'Role', NEW.Role
    ),
    CURRENT_USER(), CONNECTION_ID(),
    @app_request_id, @app_actor_member_id, @app_actor_username, @app_actor_role,
    IF(COALESCE(@app_source, '') = 'api', 'api', 'direct_db'),
    IF(COALESCE(@app_source, '') = 'api', 1, 0)
  );
END $$

DELIMITER ;