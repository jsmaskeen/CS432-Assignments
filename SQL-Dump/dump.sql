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
-- Dumping data for table `Bookings`
--

LOCK TABLES `Bookings` WRITE;
/*!40000 ALTER TABLE `Bookings` DISABLE KEYS */;
INSERT INTO `Bookings` VALUES (1,1,7,'Confirmed','tdr0z8v','tdqzm7n',28.50,'2026-02-14 10:49:47'),(2,1,9,'Confirmed','tdr0z8v','tdqzm7n',28.50,'2026-02-14 10:49:47'),(3,2,11,'Confirmed','tdr0z8v','tdr0x5p',12.30,'2026-02-14 10:49:47'),(4,3,6,'Confirmed','tdr0z8v','tdr1k8p',18.70,'2026-02-14 10:49:47'),(5,3,13,'Confirmed','tdr0z8v','tdr1k8p',18.70,'2026-02-14 10:49:47'),(6,3,15,'Confirmed','tdr0z8v','tdr1k8p',18.70,'2026-02-14 10:49:47'),(7,5,8,'Confirmed','tdr0z8v','tdr1k7n',15.20,'2026-02-14 10:49:47'),(8,5,12,'Confirmed','tdr0z8v','tdr1k7n',15.20,'2026-02-14 10:49:47'),(9,6,10,'Confirmed','tdr0z8v','tdqzr8x',32.40,'2026-02-14 10:49:47'),(10,6,14,'Confirmed','tdr0z8v','tdqzr8x',32.40,'2026-02-14 10:49:47'),(11,7,16,'Confirmed','tdr0z8v','tdr1jbw',22.10,'2026-02-14 10:49:47'),(12,7,18,'Confirmed','tdr0z8v','tdr1jbw',22.10,'2026-02-14 10:49:47'),(13,8,20,'Confirmed','tdr1k9y','tdr0z8v',14.80,'2026-02-14 10:49:47'),(14,8,22,'Confirmed','tdr1k9y','tdr0z8v',14.80,'2026-02-14 10:49:47'),(15,8,24,'Confirmed','tdr1k9y','tdr0z8v',14.80,'2026-02-14 10:49:47'),(16,9,17,'Confirmed','tdr0z8v','tdqzt2m',25.60,'2026-02-14 10:49:47'),(17,10,19,'Confirmed','tdr0z8v','tdr1p2x',19.30,'2026-02-14 10:49:47'),(18,10,21,'Confirmed','tdr0z8v','tdr1p2x',19.30,'2026-02-14 10:49:47'),(19,11,2,'Confirmed','tdqzm7n','tdr0z8v',28.50,'2026-02-14 10:49:47'),(20,11,4,'Confirmed','tdqzm7n','tdr0z8v',28.50,'2026-02-14 10:49:47'),(21,11,5,'Confirmed','tdqzm7n','tdr0z8v',28.50,'2026-02-14 10:49:47'),(22,12,23,'Confirmed','tdr0z8v','tdr2n5p',16.90,'2026-02-14 10:49:47'),(23,12,25,'Confirmed','tdr0z8v','tdr2n5p',16.90,'2026-02-14 10:49:47'),(24,13,1,'Confirmed','tdr0z8v','tdqzv5q',27.80,'2026-02-14 10:49:47'),(25,13,3,'Confirmed','tdr0z8v','tdqzv5q',27.80,'2026-02-14 10:49:47'),(26,14,6,'Confirmed','tdr1k7n','tdr0z8v',15.20,'2026-02-14 10:49:47'),(27,14,8,'Confirmed','tdr1k7n','tdr0z8v',15.20,'2026-02-14 10:49:47'),(28,14,10,'Confirmed','tdr1k7n','tdr0z8v',15.20,'2026-02-14 10:49:47'),(29,16,2,'Confirmed','tdr0z8v','tdr0x5p',12.30,'2026-02-14 10:49:47'),(30,16,7,'Confirmed','tdr0z8v','tdr0x5p',12.30,'2026-02-14 10:49:47'),(31,16,11,'Confirmed','tdr0z8v','tdr0x5p',12.30,'2026-02-14 10:49:47'),(32,16,13,'Confirmed','tdr0z8v','tdr0x5p',12.30,'2026-02-14 10:49:47'),(33,16,15,'Confirmed','tdr0z8v','tdr0x5p',12.30,'2026-02-14 10:49:47'),(34,17,12,'Confirmed','tdr0z8v','tdqzy0t',29.40,'2026-02-14 10:49:47'),(35,17,14,'Confirmed','tdr0z8v','tdqzy0t',29.40,'2026-02-14 10:49:47'),(36,18,4,'Confirmed','tdqzm7n','tdr0z8v',28.50,'2026-02-14 10:49:47'),(37,18,9,'Confirmed','tdqzm7n','tdr0z8v',28.50,'2026-02-14 10:49:47'),(38,18,19,'Confirmed','tdqzm7n','tdr0z8v',28.50,'2026-02-14 10:49:47'),(39,19,21,'Confirmed','tdr0z8v','tdr1kcd',13.70,'2026-02-14 10:49:47'),(40,20,1,'Confirmed','tdr0z8v','tdqzu7p',24.20,'2026-02-14 10:49:47'),(41,20,5,'Confirmed','tdr0z8v','tdqzu7p',24.20,'2026-02-14 10:49:47'),(42,20,12,'Confirmed','tdr0z8v','tdqzu7p',24.20,'2026-02-14 10:49:47'),(43,20,16,'Confirmed','tdr0z8v','tdqzu7p',24.20,'2026-02-14 10:49:47'),(44,23,3,'Confirmed','tdr0z8v','tdr1kb5',11.50,'2026-02-14 10:49:47'),(45,23,7,'Confirmed','tdr0z8v','tdr1kb5',11.50,'2026-02-14 10:49:47'),(46,24,1,'Confirmed','tdr0z8v','tdqzm7n',28.50,'2026-02-14 10:49:47'),(47,24,3,'Confirmed','tdr0z8v','tdqzm7n',28.50,'2026-02-14 10:49:47'),(48,24,6,'Confirmed','tdr0z8v','tdqzm7n',28.50,'2026-02-14 10:49:47'),(49,24,9,'Confirmed','tdr0z8v','tdqzm7n',28.50,'2026-02-14 10:49:47'),(50,24,11,'Confirmed','tdr0z8v','tdqzm7n',28.50,'2026-02-14 10:49:47'),(51,25,2,'Confirmed','tdr0z8v','tdr1k6m',14.60,'2026-02-14 10:49:47'),(52,25,8,'Confirmed','tdr0z8v','tdr1k6m',14.60,'2026-02-14 10:49:47'),(53,25,18,'Confirmed','tdr0z8v','tdr1k6m',14.60,'2026-02-14 10:49:47');
/*!40000 ALTER TABLE `Bookings` ENABLE KEYS */;
UNLOCK TABLES;

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
-- Dumping data for table `Cost_Settlements`
--

LOCK TABLES `Cost_Settlements` WRITE;
/*!40000 ALTER TABLE `Cost_Settlements` DISABLE KEYS */;
INSERT INTO `Cost_Settlements` VALUES (1,1,356.25,'Settled'),(2,2,356.25,'Settled'),(3,3,123.00,'Settled'),(4,4,280.50,'Settled'),(5,5,280.50,'Settled'),(6,6,280.50,'Settled'),(7,7,152.00,'Unpaid'),(8,8,152.00,'Unpaid'),(9,9,421.20,'Unpaid'),(10,10,421.20,'Unpaid'),(11,11,309.40,'Unpaid'),(12,12,309.40,'Unpaid'),(13,13,177.60,'Unpaid'),(14,14,177.60,'Unpaid'),(15,15,177.60,'Unpaid'),(16,16,281.60,'Unpaid'),(17,17,257.70,'Unpaid'),(18,18,257.70,'Unpaid'),(19,19,342.00,'Settled'),(20,20,356.25,'Settled'),(21,21,356.25,'Settled'),(22,22,177.75,'Unpaid'),(23,23,177.75,'Unpaid'),(24,24,333.60,'Unpaid'),(25,25,333.60,'Unpaid'),(26,26,182.40,'Settled'),(27,27,182.40,'Settled'),(28,28,182.40,'Settled'),(29,29,123.00,'Settled'),(30,30,147.60,'Settled'),(31,31,147.60,'Settled'),(32,32,147.60,'Settled'),(33,33,147.60,'Settled'),(34,34,411.60,'Unpaid'),(35,35,411.60,'Unpaid'),(36,36,356.25,'Settled'),(37,37,356.25,'Settled'),(38,38,356.25,'Settled'),(39,39,150.70,'Unpaid'),(40,40,314.60,'Settled'),(41,41,314.60,'Settled'),(42,42,314.60,'Settled'),(43,43,314.60,'Settled'),(44,44,138.00,'Unpaid'),(45,45,138.00,'Unpaid'),(46,46,285.00,'Settled'),(47,47,285.00,'Settled'),(48,48,285.00,'Settled'),(49,49,285.00,'Settled'),(50,50,285.00,'Settled'),(51,51,197.10,'Settled'),(52,52,197.10,'Settled'),(53,53,197.10,'Settled');
/*!40000 ALTER TABLE `Cost_Settlements` ENABLE KEYS */;
UNLOCK TABLES;

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
-- Dumping data for table `Locations`
--

LOCK TABLES `Locations` WRITE;
/*!40000 ALTER TABLE `Locations` DISABLE KEYS */;
INSERT INTO `Locations` VALUES (1,'IITGN Main Gate','Campus','tdr0z8v'),(2,'Academic Block 1','Campus','tdr0z8w'),(3,'Academic Block 2','Campus','tdr0z8x'),(4,'Library','Campus','tdr0z8y'),(5,'Sports Complex','Campus','tdr0z8z'),(6,'Hostel Area','Campus','tdr0z90'),(7,'Mess 1','Campus','tdr0z91'),(8,'Mess 2','Campus','tdr0z92'),(9,'Student Activity Center','Campus','tdr0z93'),(10,'Medical Center','Campus','tdr0z94'),(11,'Gandhinagar Railway Station','Transport','tdr0x5p'),(12,'Ahmedabad Airport','Transport','tdqzm7n'),(13,'Palaj Bus Stand','Transport','tdr0z2q'),(14,'Indroda Circle','City','tdr1kb5'),(15,'Infocity','City','tdr1k8p'),(16,'Gift City','City','tdr1p2x'),(17,'Sector 21 Gandhinagar','City','tdr1k9y'),(18,'Akshardham Temple','Tourist','tdr1jbw'),(19,'Mahatma Mandir','Event','tdr1kcd'),(20,'City Pulse Mall','Shopping','tdr1k7n'),(21,'Reliance Mall Gandhinagar','Shopping','tdr1k6m'),(22,'Adalaj Stepwell','Tourist','tdr2n5p'),(23,'Sabarmati Riverfront','Tourist','tdqzr8x'),(24,'Law Garden','City','tdqzt2m'),(25,'Paldi','City','tdqzs9n'),(26,'Vastrapur','City','tdqzu7p'),(27,'SG Highway','City','tdqzv5q'),(28,'Thaltej','City','tdqzw3r'),(29,'Navrangpura','City','tdqzx1s'),(30,'CG Road','City','tdqzy0t');
/*!40000 ALTER TABLE `Locations` ENABLE KEYS */;
UNLOCK TABLES;

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
-- Dumping data for table `Members`
--

LOCK TABLES `Members` WRITE;
/*!40000 ALTER TABLE `Members` DISABLE KEYS */;
INSERT INTO `Members` VALUES (1,'oauth_aarsh_2024','aarsh.patel@iitgn.ac.in','Aarsh Patel',4.8,'9876543210','2026-02-14 10:49:47','Male'),(2,'oauth_abhinav_2024','abhinav.sharma@iitgn.ac.in','Abhinav Sharma',4.5,'9876543211','2026-02-14 10:49:47','Male'),(3,'oauth_romit_2024','romit.gupta@iitgn.ac.in','Romit Gupta',4.7,'9876543212','2026-02-14 10:49:47','Male'),(4,'oauth_karan_2024','karan.singh@iitgn.ac.in','Karan Singh',4.6,'9876543213','2026-02-14 10:49:47','Male'),(5,'oauth_jaskirat_2024','jaskirat.kaur@iitgn.ac.in','Jaskirat Kaur',4.9,'9876543214','2026-02-14 10:49:47','Female'),(6,'oauth_priya_2024','priya.mehta@iitgn.ac.in','Priya Mehta',4.4,'9876543215','2026-02-14 10:49:47','Female'),(7,'oauth_rahul_2024','rahul.verma@iitgn.ac.in','Rahul Verma',4.3,'9876543216','2026-02-14 10:49:47','Male'),(8,'oauth_sneha_2024','sneha.joshi@iitgn.ac.in','Sneha Joshi',4.7,'9876543217','2026-02-14 10:49:47','Female'),(9,'oauth_arjun_2024','arjun.reddy@iitgn.ac.in','Arjun Reddy',4.2,'9876543218','2026-02-14 10:49:47','Male'),(10,'oauth_ananya_2024','ananya.iyer@iitgn.ac.in','Ananya Iyer',4.8,'9876543219','2026-02-14 10:49:47','Female'),(11,'oauth_vikram_2024','vikram.nair@iitgn.ac.in','Vikram Nair',4.1,'9876543220','2026-02-14 10:49:47','Male'),(12,'oauth_ishita_2024','ishita.desai@iitgn.ac.in','Ishita Desai',4.6,'9876543221','2026-02-14 10:49:47','Female'),(13,'oauth_aditya_2024','aditya.kumar@iitgn.ac.in','Aditya Kumar',4.5,'9876543222','2026-02-14 10:49:47','Male'),(14,'oauth_divya_2024','divya.rao@iitgn.ac.in','Divya Rao',4.9,'9876543223','2026-02-14 10:49:47','Female'),(15,'oauth_harsh_2024','harsh.agarwal@iitgn.ac.in','Harsh Agarwal',4.0,'9876543224','2026-02-14 10:49:47','Male'),(16,'oauth_kavya_2024','kavya.pillai@iitgn.ac.in','Kavya Pillai',4.7,'9876543225','2026-02-14 10:49:47','Female'),(17,'oauth_rohan_2024','rohan.malhotra@iitgn.ac.in','Rohan Malhotra',4.4,'9876543226','2026-02-14 10:49:47','Male'),(18,'oauth_tanvi_2024','tanvi.bhat@iitgn.ac.in','Tanvi Bhat',4.8,'9876543227','2026-02-14 10:49:47','Female'),(19,'oauth_siddharth_2024','siddharth.das@iitgn.ac.in','Siddharth Das',4.3,'9876543228','2026-02-14 10:49:47','Male'),(20,'oauth_nisha_2024','nisha.chawla@iitgn.ac.in','Nisha Chawla',4.6,'9876543229','2026-02-14 10:49:47','Female'),(21,'oauth_kunal_2024','kunal.shah@iitgn.ac.in','Kunal Shah',4.5,'9876543230','2026-02-14 10:49:47','Male'),(22,'oauth_riya_2024','riya.banerjee@iitgn.ac.in','Riya Banerjee',4.7,'9876543231','2026-02-14 10:49:47','Female'),(23,'oauth_varun_2024','varun.menon@iitgn.ac.in','Varun Menon',4.2,'9876543232','2026-02-14 10:49:47','Male'),(24,'oauth_pooja_2024','pooja.saxena@iitgn.ac.in','Pooja Saxena',4.8,'9876543233','2026-02-14 10:49:47','Female'),(25,'oauth_manish_2024','manish.tiwari@iitgn.ac.in','Manish Tiwari',4.4,'9876543234','2026-02-14 10:49:47','Male');
/*!40000 ALTER TABLE `Members` ENABLE KEYS */;
UNLOCK TABLES;

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
-- Dumping data for table `Reputation_Reviews`
--

LOCK TABLES `Reputation_Reviews` WRITE;
/*!40000 ALTER TABLE `Reputation_Reviews` DISABLE KEYS */;
INSERT INTO `Reputation_Reviews` VALUES (1,11,2,11,5,'Great host! Very punctual and smooth ride.','2026-02-14 10:49:47'),(2,11,4,11,5,'Vikram was super accommodating. Would ride again!','2026-02-14 10:49:47'),(3,11,5,11,5,'Perfect ride, great music too!','2026-02-14 10:49:47'),(4,11,11,2,5,'Abhinav was a pleasant passenger.','2026-02-14 10:49:47'),(5,11,11,4,5,'Karan was very respectful and on time.','2026-02-14 10:49:47'),(6,11,11,5,4,'Jaskirat was great, would ride with her again.','2026-02-14 10:49:47'),(7,16,2,16,5,'Early morning ride but Kavya made it comfortable. Highly recommend!','2026-02-14 10:49:47'),(8,16,7,16,5,'Super organized and on time despite the early hour.','2026-02-14 10:49:47'),(9,16,11,16,5,'Kavya is an excellent host! Very friendly.','2026-02-14 10:49:47'),(10,16,13,16,4,'Good ride, would have appreciated slightly slower driving.','2026-02-14 10:49:47'),(11,16,15,16,5,'Perfect! Made it to my train with time to spare.','2026-02-14 10:49:47'),(12,16,16,2,5,'Abhinav was ready on time and very pleasant.','2026-02-14 10:49:47'),(13,16,16,7,5,'Rahul was a great passenger!','2026-02-14 10:49:47'),(14,16,16,11,5,'Vikram was wonderful to drive with.','2026-02-14 10:49:47'),(15,16,16,13,5,'Aditya brought energy drinks as promised!','2026-02-14 10:49:47'),(16,16,16,15,4,'Harsh was good, would ride together again.','2026-02-14 10:49:47'),(17,20,1,20,5,'Nisha is an amazing driver! Very safe and comfortable ride.','2026-02-14 10:49:47'),(18,20,5,20,5,'Really enjoyed the ride. Great conversation!','2026-02-14 10:49:47'),(19,20,12,20,5,'Punctual and professional. Thanks Nisha!','2026-02-14 10:49:47'),(20,20,16,20,4,'Good ride overall. Music could have been better but that\'s minor.','2026-02-14 10:49:47'),(21,20,20,1,5,'Aarsh was respectful and easy to talk to.','2026-02-14 10:49:47'),(22,20,20,5,5,'Jaskirat was wonderful! Great company on the ride.','2026-02-14 10:49:47'),(23,20,20,12,5,'Ishita was very pleasant throughout.','2026-02-14 10:49:47'),(24,20,20,16,5,'Kavya was a great passenger.','2026-02-14 10:49:47'),(25,24,1,24,5,'Pooja got us to the airport safely and on time. Excellent!','2026-02-14 10:49:47'),(26,24,3,24,5,'Very professional and courteous. Great ride!','2026-02-14 10:49:47'),(27,24,6,24,4,'Good ride, but a bit too much AC for my liking.','2026-02-14 10:49:47'),(28,24,9,24,5,'Pooja is a fantastic host! Would definitely ride again.','2026-02-14 10:49:47'),(29,24,11,24,5,'Perfect early morning ride. Thanks Pooja!','2026-02-14 10:49:47'),(30,24,24,1,5,'Aarsh was great! Very respectful.','2026-02-14 10:49:47'),(31,24,24,3,5,'Romit was an excellent passenger.','2026-02-14 10:49:47'),(32,24,24,6,5,'Priya was lovely to have in the car.','2026-02-14 10:49:47'),(33,24,24,9,4,'Arjun was good, slightly late but made up for it.','2026-02-14 10:49:47'),(34,24,24,11,5,'Vikram was wonderful as always!','2026-02-14 10:49:47'),(35,11,2,4,5,'Karan was great company on the ride!','2026-02-14 10:49:47'),(36,11,4,2,5,'Abhinav was super friendly!','2026-02-14 10:49:47'),(37,16,7,13,4,'Aditya was cool, great to ride with.','2026-02-14 10:49:47'),(38,20,1,5,5,'Jaskirat has great taste in music!','2026-02-14 10:49:47'),(39,24,3,9,4,'Arjun was fun to talk to during the ride.','2026-02-14 10:49:47');
/*!40000 ALTER TABLE `Reputation_Reviews` ENABLE KEYS */;
UNLOCK TABLES;

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
-- Dumping data for table `Ride_Chat`
--

LOCK TABLES `Ride_Chat` WRITE;
/*!40000 ALTER TABLE `Ride_Chat` DISABLE KEYS */;
INSERT INTO `Ride_Chat` VALUES (1,1,1,'Hey everyone! Flight at 8 AM, leaving campus at 6. We should reach by 7:15.','2026-02-14 10:49:47'),(2,1,7,'Perfect! I have a 9 AM flight. Thanks for organizing this Aarsh!','2026-02-14 10:49:47'),(3,1,9,'Count me in. Should I bring coffee for everyone?','2026-02-14 10:49:47'),(4,1,1,'That would be awesome! Meet at main gate at 5:55 sharp.','2026-02-14 10:49:47'),(5,1,7,'Got it. See you guys tomorrow morning!','2026-02-14 10:49:47'),(6,2,2,'Going to railway station for the 8:30 train. Anyone else?','2026-02-14 10:49:47'),(7,2,11,'Yes! I have the 9 AM train. Can you pick me up from hostel area?','2026-02-14 10:49:47'),(8,2,2,'Sure thing! Will be there at 7:25.','2026-02-14 10:49:47'),(9,3,3,'Heading to Infocity for internship interview. Ride is now full!','2026-02-14 10:49:47'),(10,3,6,'Thanks Romit! What time are we leaving exactly?','2026-02-14 10:49:47'),(11,3,3,'8 AM sharp from main gate. Traffic can be unpredictable.','2026-02-14 10:49:47'),(12,3,13,'Cool. I\'ll be there 5 minutes early.','2026-02-14 10:49:47'),(13,3,15,'Same here. Good luck with your interviews everyone!','2026-02-14 10:49:47'),(14,5,5,'Mall trip for some shopping! Leaving at 4 PM.','2026-02-14 10:49:47'),(15,5,8,'Great! I need to buy some books. How long will we stay?','2026-02-14 10:49:47'),(16,5,5,'Around 2-3 hours probably. We can grab dinner there too.','2026-02-14 10:49:47'),(17,5,12,'Sounds good! Can we stop by the electronics store?','2026-02-14 10:49:47'),(18,5,5,'Of course! Let\'s make a list of stores we all need to visit.','2026-02-14 10:49:47'),(19,6,6,'Sunday evening at Sabarmati Riverfront! Who\'s in?','2026-02-14 10:49:47'),(20,6,10,'Me! I love the sunset views there.','2026-02-14 10:49:47'),(21,6,14,'Count me in. Should we plan to have dinner nearby?','2026-02-14 10:49:47'),(22,6,6,'Yes! There are some great restaurants in that area. Let\'s decide once we\'re there.','2026-02-14 10:49:47'),(23,11,11,'Just landed! Picking up luggage now. Will be at pickup point in 15 mins.','2026-02-14 10:49:47'),(24,11,2,'Great! We\'re already waiting at Gate 3.','2026-02-14 10:49:47'),(25,11,4,'Thanks for organizing this Vikram!','2026-02-14 10:49:47'),(26,11,11,'No problem! On my way now.','2026-02-14 10:49:47'),(27,11,5,'See you soon!','2026-02-14 10:49:47'),(28,13,13,'Going to SG Highway for project meeting. Leaving at 3 PM.','2026-02-14 10:49:47'),(29,13,1,'Perfect timing! I have a meeting there too at 4.','2026-02-14 10:49:47'),(30,13,3,'Can we stop at the electronics market on the way back?','2026-02-14 10:49:47'),(31,13,13,'Sure! We can plan the return around 6 PM.','2026-02-14 10:49:47'),(32,16,16,'Early morning ride to railway station. 5:30 AM departure!','2026-02-14 10:49:47'),(33,16,2,'That\'s early! But my train is at 7 so I\'m in.','2026-02-14 10:49:47'),(34,16,7,'Same. Thanks for organizing Kavya.','2026-02-14 10:49:47'),(35,16,16,'No worries! Let\'s all set alarms ?','2026-02-14 10:49:47'),(36,16,13,'I\'ll bring energy drinks for everyone!','2026-02-14 10:49:47'),(37,16,15,'You\'re a lifesaver! See you all at the gate.','2026-02-14 10:49:47');
/*!40000 ALTER TABLE `Ride_Chat` ENABLE KEYS */;
UNLOCK TABLES;

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
-- Dumping data for table `Ride_Participants`
--

LOCK TABLES `Ride_Participants` WRITE;
/*!40000 ALTER TABLE `Ride_Participants` DISABLE KEYS */;
INSERT INTO `Ride_Participants` VALUES (1,1,1,'Host','2026-02-14 10:49:47'),(2,1,7,'Passenger','2026-02-14 10:49:47'),(3,1,9,'Passenger','2026-02-14 10:49:47'),(4,2,2,'Host','2026-02-14 10:49:47'),(5,2,11,'Passenger','2026-02-14 10:49:47'),(6,3,3,'Host','2026-02-14 10:49:47'),(7,3,6,'Passenger','2026-02-14 10:49:47'),(8,3,13,'Passenger','2026-02-14 10:49:47'),(9,3,15,'Passenger','2026-02-14 10:49:47'),(10,4,4,'Host','2026-02-14 10:49:47'),(11,5,5,'Host','2026-02-14 10:49:47'),(12,5,8,'Passenger','2026-02-14 10:49:47'),(13,5,12,'Passenger','2026-02-14 10:49:47'),(14,6,6,'Host','2026-02-14 10:49:47'),(15,6,10,'Passenger','2026-02-14 10:49:47'),(16,6,14,'Passenger','2026-02-14 10:49:47'),(17,7,7,'Host','2026-02-14 10:49:47'),(18,7,16,'Passenger','2026-02-14 10:49:47'),(19,7,18,'Passenger','2026-02-14 10:49:47'),(20,8,8,'Host','2026-02-14 10:49:47'),(21,8,20,'Passenger','2026-02-14 10:49:47'),(22,8,22,'Passenger','2026-02-14 10:49:47'),(23,8,24,'Passenger','2026-02-14 10:49:47'),(24,9,9,'Host','2026-02-14 10:49:47'),(25,9,17,'Passenger','2026-02-14 10:49:47'),(26,10,10,'Host','2026-02-14 10:49:47'),(27,10,19,'Passenger','2026-02-14 10:49:47'),(28,10,21,'Passenger','2026-02-14 10:49:47'),(29,11,11,'Host','2026-02-14 10:49:47'),(30,11,2,'Passenger','2026-02-14 10:49:47'),(31,11,4,'Passenger','2026-02-14 10:49:47'),(32,11,5,'Passenger','2026-02-14 10:49:47'),(33,12,12,'Host','2026-02-14 10:49:47'),(34,12,23,'Passenger','2026-02-14 10:49:47'),(35,12,25,'Passenger','2026-02-14 10:49:47'),(36,13,13,'Host','2026-02-14 10:49:47'),(37,13,1,'Passenger','2026-02-14 10:49:47'),(38,13,3,'Passenger','2026-02-14 10:49:47'),(39,14,14,'Host','2026-02-14 10:49:47'),(40,14,6,'Passenger','2026-02-14 10:49:47'),(41,14,8,'Passenger','2026-02-14 10:49:47'),(42,14,10,'Passenger','2026-02-14 10:49:47'),(43,15,15,'Host','2026-02-14 10:49:47'),(44,16,16,'Host','2026-02-14 10:49:47'),(45,16,2,'Passenger','2026-02-14 10:49:47'),(46,16,7,'Passenger','2026-02-14 10:49:47'),(47,16,11,'Passenger','2026-02-14 10:49:47'),(48,16,13,'Passenger','2026-02-14 10:49:47'),(49,16,15,'Passenger','2026-02-14 10:49:47'),(50,17,17,'Host','2026-02-14 10:49:47'),(51,17,12,'Passenger','2026-02-14 10:49:47'),(52,17,14,'Passenger','2026-02-14 10:49:47'),(53,18,18,'Host','2026-02-14 10:49:47'),(54,18,4,'Passenger','2026-02-14 10:49:47'),(55,18,9,'Passenger','2026-02-14 10:49:47'),(56,18,19,'Passenger','2026-02-14 10:49:47'),(57,19,19,'Host','2026-02-14 10:49:47'),(58,19,21,'Passenger','2026-02-14 10:49:47'),(59,20,20,'Host','2026-02-14 10:49:47'),(60,20,1,'Passenger','2026-02-14 10:49:47'),(61,20,5,'Passenger','2026-02-14 10:49:47'),(62,20,12,'Passenger','2026-02-14 10:49:47'),(63,20,16,'Passenger','2026-02-14 10:49:47'),(64,21,21,'Host','2026-02-14 10:49:47'),(65,22,22,'Host','2026-02-14 10:49:47'),(66,23,23,'Host','2026-02-14 10:49:47'),(67,23,3,'Passenger','2026-02-14 10:49:47'),(68,23,7,'Passenger','2026-02-14 10:49:47'),(69,24,24,'Host','2026-02-14 10:49:47'),(70,24,1,'Passenger','2026-02-14 10:49:47'),(71,24,3,'Passenger','2026-02-14 10:49:47'),(72,24,6,'Passenger','2026-02-14 10:49:47'),(73,24,9,'Passenger','2026-02-14 10:49:47'),(74,24,11,'Passenger','2026-02-14 10:49:47'),(75,25,25,'Host','2026-02-14 10:49:47'),(76,25,2,'Passenger','2026-02-14 10:49:47'),(77,25,8,'Passenger','2026-02-14 10:49:47'),(78,25,18,'Passenger','2026-02-14 10:49:47');
/*!40000 ALTER TABLE `Ride_Participants` ENABLE KEYS */;
UNLOCK TABLES;

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
  `Ride_Status` enum('Open','Full','Cancelled','Completed') NOT NULL DEFAULT 'Open',
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
-- Dumping data for table `Rides`
--

LOCK TABLES `Rides` WRITE;
/*!40000 ALTER TABLE `Rides` DISABLE KEYS */;
INSERT INTO `Rides` VALUES (1,1,'ts5h3k2','ts5h7n8','2024-02-15 06:00:00','Sedan',4,2,12.50,'Open','2026-02-14 10:49:47'),(2,2,'ts5h3k2','ts5h8p4','2024-02-15 07:30:00','SUV',6,4,10.00,'Open','2026-02-14 10:49:47'),(3,3,'ts5h3k2','ts5j0d6','2024-02-15 08:00:00','Hatchback',4,1,15.00,'Full','2026-02-14 10:49:47'),(4,4,'ts5h7n8','ts5h3k2','2024-02-15 14:00:00','Sedan',4,3,12.50,'Open','2026-02-14 10:49:47'),(5,5,'ts5h3k2','ts5j1c5','2024-02-15 16:00:00','SUV',6,3,10.00,'Open','2026-02-14 10:49:47'),(6,6,'ts5h3k2','ts5gzu9','2024-02-15 17:00:00','Sedan',4,2,13.00,'Open','2026-02-14 10:49:47'),(7,7,'ts5h3k2','ts5j2m7','2024-02-16 09:00:00','Hatchback',4,2,14.00,'Open','2026-02-14 10:49:47'),(8,8,'ts5j0f3','ts5h3k2','2024-02-16 08:00:00','Sedan',4,1,12.00,'Full','2026-02-14 10:49:47'),(9,9,'ts5h3k2','ts5gvv4','2024-02-16 18:00:00','SUV',6,4,11.00,'Open','2026-02-14 10:49:47'),(10,10,'ts5h3k2','ts5jbq8','2024-02-16 10:00:00','Sedan',4,2,13.50,'Open','2026-02-14 10:49:47'),(11,11,'ts5h7n8','ts5h3k2','2024-02-14 20:00:00','Hatchback',4,0,12.00,'Completed','2026-02-14 10:49:47'),(12,12,'ts5h3k2','ts5k1p6','2024-02-17 11:00:00','SUV',6,3,10.50,'Open','2026-02-14 10:49:47'),(13,13,'ts5h3k2','ts5gwx7','2024-02-17 15:00:00','Sedan',4,2,12.00,'Open','2026-02-14 10:49:47'),(14,14,'ts5j1c5','ts5h3k2','2024-02-17 21:00:00','Hatchback',4,1,13.00,'Full','2026-02-14 10:49:47'),(15,15,'ts5h3k2','ts5gxy5','2024-02-18 07:00:00','Sedan',4,3,12.50,'Open','2026-02-14 10:49:47'),(16,16,'ts5h3k2','ts5h8p4','2024-02-14 05:30:00','SUV',6,0,10.00,'Completed','2026-02-14 10:49:47'),(17,17,'ts5h3k2','ts5gzs2','2024-02-18 19:00:00','Hatchback',4,2,14.00,'Open','2026-02-14 10:49:47'),(18,18,'ts5h7n8','ts5h3k2','2024-02-18 22:00:00','Sedan',4,1,12.50,'Full','2026-02-14 10:49:47'),(19,19,'ts5h3k2','ts5j2t9','2024-02-19 10:00:00','SUV',6,4,11.00,'Open','2026-02-14 10:49:47'),(20,20,'ts5h3k2','ts5gvt8','2024-02-13 08:00:00','Sedan',4,0,13.00,'Completed','2026-02-14 10:49:47'),(21,21,'ts5j0d6','ts5h3k2','2024-02-19 18:00:00','Hatchback',4,3,15.00,'Open','2026-02-14 10:49:47'),(22,22,'ts5h3k2','ts5gwr4','2024-02-20 12:00:00','SUV',6,5,10.50,'Open','2026-02-14 10:49:47'),(23,23,'ts5h3k2','ts5j2r3','2024-02-20 16:00:00','Sedan',4,2,12.00,'Open','2026-02-14 10:49:47'),(24,24,'ts5h3k2','ts5h7n8','2024-02-12 04:30:00','SUV',6,0,10.00,'Completed','2026-02-14 10:49:47'),(25,25,'ts5h3k2','ts5j1b9','2024-02-21 14:00:00','Hatchback',4,1,13.50,'Full','2026-02-14 10:49:47');
/*!40000 ALTER TABLE `Rides` ENABLE KEYS */;
UNLOCK TABLES;

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
-- Dumping data for table `Saved_Addresses`
--

LOCK TABLES `Saved_Addresses` WRITE;
/*!40000 ALTER TABLE `Saved_Addresses` DISABLE KEYS */;
INSERT INTO `Saved_Addresses` VALUES (1,1,'Home',1),(2,1,'Favorite Restaurant',20),(3,2,'Home',6),(4,2,'Airport',12),(5,3,'Home',6),(6,3,'Railway Station',11),(7,4,'Home',6),(8,4,'Mall',21),(9,5,'Home',6),(10,5,'Temple',18),(11,6,'Home',6),(12,6,'Infocity Office',15),(13,7,'Home',6),(14,8,'Home',6),(15,8,'Gift City',16),(16,9,'Home',6),(17,10,'Home',6),(18,10,'CG Road',30),(19,11,'Home',6),(20,12,'Home',6),(21,12,'Adalaj',22),(22,13,'Home',6),(23,14,'Home',6),(24,15,'Home',6),(25,16,'Home',6);
/*!40000 ALTER TABLE `Saved_Addresses` ENABLE KEYS */;
UNLOCK TABLES;

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
-- Dumping data for table `User_Preferences`
--

LOCK TABLES `User_Preferences` WRITE;
/*!40000 ALTER TABLE `User_Preferences` DISABLE KEYS */;
INSERT INTO `User_Preferences` VALUES (1,1,'Any',1,'Bollywood'),(2,2,'Any',1,'Rock'),(3,3,'Any',0,'Pop'),(4,4,'Any',1,'Hip Hop'),(5,5,'Same-Gender Only',1,'Classical'),(6,6,'Same-Gender Only',1,'Indie'),(7,7,'Any',0,'Electronic'),(8,8,'Same-Gender Only',1,'Bollywood'),(9,9,'Any',1,'Rock'),(10,10,'Same-Gender Only',1,'Pop'),(11,11,'Any',0,'Jazz'),(12,12,'Same-Gender Only',1,'Bollywood'),(13,13,'Any',1,'Hip Hop'),(14,14,'Same-Gender Only',0,'Classical'),(15,15,'Any',1,'Rock'),(16,16,'Same-Gender Only',1,'Pop'),(17,17,'Any',0,'Bollywood'),(18,18,'Same-Gender Only',1,'Indie'),(19,19,'Any',1,'Electronic'),(20,20,'Same-Gender Only',0,'Jazz'),(21,21,'Any',1,'Hip Hop'),(22,22,'Same-Gender Only',1,'Bollywood'),(23,23,'Any',0,'Rock'),(24,24,'Same-Gender Only',1,'Classical'),(25,25,'Any',1,'Pop');
/*!40000 ALTER TABLE `User_Preferences` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-14 16:22:03
