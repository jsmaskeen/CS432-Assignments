USE cabSharing;

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
