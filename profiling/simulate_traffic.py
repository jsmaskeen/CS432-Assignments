import requests
import string
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from tqdm import tqdm
import os

def load_env(env_path: Path) -> dict[str, str]:
    values = {}
    if not env_path.exists():
        return values
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_VALUES = load_env(ROOT_DIR / "backend" / ".env")
MYSQL_USER = ENV_VALUES.get("MYSQL_USER", "root")
MYSQL_PASSWORD = ENV_VALUES.get("MYSQL_PASSWORD", "")

# Get database back to normal state before running this script.
dump_path = ROOT_DIR / "SQL-Dump" / "dump.sql"
if MYSQL_PASSWORD:
    os.environ["MYSQL_PWD"] = MYSQL_PASSWORD
os.system(f"mysql -u{MYSQL_USER} cabSharing < {dump_path}")


# Update this if your backend runs on a different port
BASE_URL = "http://127.0.0.1:8000/api/v1"

# Adjust these settings depending on how quickly you want to seed data
NUM_USERS = 100
RIDES_PER_USER_HOSTED = 200
SEARCH_REQUESTS = 100

def generate_random_string(length=8):
    """Utility to generate dummy usernames and geohashes"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def run_simulation():
    print(f"--- Starting Dummy Virtual Replay ---")
    print(f"Goal: Register {NUM_USERS} users, each listing {RIDES_PER_USER_HOSTED} rides.")
    print(f"This will dump {NUM_USERS * RIDES_PER_USER_HOSTED} realistic rows into the database.\n")
    
    session = requests.Session()
    tokens = []

    # 1. EMULATE USERS REGISTERING & LOGGING IN
    print("Step 1: Emulating user registration...")
    for _ in tqdm(range(NUM_USERS), desc="Registering users"):
        username = f"user_{generate_random_string()}"
        password = "password123!"
        email = f"{username}@iitgn.ac.in" # Has to match the backend validator
        
        # Register API Call
        reg_url = f"{BASE_URL}/auth/register"
        random_phone = "".join(random.choices(string.digits, k=10))
        res = session.post(reg_url, json={
            "username": username,
            "password": password,
            "email": email,
            "full_name": "Virtual Replay User",
            "phone_number": random_phone,
            "gender": random.choice(["Male", "Female", "Other"])
        })
        
        if res.status_code == 201:
            token = res.json().get("access_token")
            tokens.append(token)
        else:
            print(f"Failed to register user. Status: {res.status_code} Body: {res.text}")

    print(f"  -> Successfully registered {len(tokens)} dummy users.\n")
    
    # 2. EMULATE USERS POSTING RIDES
    print("Step 2: Emulating users actively creating cabs/rides...")
    successful_rides = 0
    
    for idx, token in enumerate(tokens):
        headers = {"Authorization": f"Bearer {token}"}
        
        for _ in tqdm(range(RIDES_PER_USER_HOSTED), desc=f"User {idx+1} creating rides"):
            # Create a mock future date
            random_days_ahead = random.randint(1, 30)
            dep_time = (datetime.now() + timedelta(days=random_days_ahead)).isoformat()
            
            res = session.post(f"{BASE_URL}/rides", headers=headers, json={
                "start_geohash": generate_random_string(6),
                "end_geohash": generate_random_string(6),
                "departure_time": dep_time,
                "vehicle_type": random.choice(["Car", "Bike", "Auto"]),
                "max_capacity": random.randint(1, 4),
                "base_fare_per_km": random.randint(10, 50)
            })
            
            if res.status_code == 201:
                successful_rides += 1
                
        if (idx+1) % 5 == 0:
            print(f"  -> {idx+1} users finished creating their rides.")

    print(f"  -> Pre-loaded Database with {successful_rides} dummy rides.\n")

    # 3. EMULATING HEAVY READING/SEARCHING TO BENCHMARK (YOUR OPTIMIZATION!)
    print(f"Step 3: Simulating a surge in traffic! Users are aggressively searching for open rides.")
    print(f"Sending {SEARCH_REQUESTS} search requests to /rides...\n")
    
    response_times = []
    
    for _ in range(SEARCH_REQUESTS):
        start_time = time.time()
        
        # Hit the heavy endpoint where we optimized with indexing logic
        res = session.get(f"{BASE_URL}/rides?only_open=True&limit=100")
        
        if res.status_code == 200:
            response_times.append((time.time() - start_time) * 1000) # milliseconds
    
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        fastest = min(response_times)
        slowest = max(response_times)
        
        print("=========================================")
        print("          BENCHMARK RESULTS              ")
        print("=========================================")
        print(f" Total Search Queries: {SEARCH_REQUESTS}")
        print(f" Average Response Time: {avg_time:.2f} ms")
        print(f" Fastest Query Time:    {fastest:.2f} ms")
        print(f" Slowest Query Time:    {slowest:.2f} ms")
        print("=========================================")
        print("\nIMPORTANT FOR ASSIGNMENT:")
        print("Note these numbers down! Then run this script AGAIN after adding the index.")
        print("The Average Response Time should be significantly lower next time.")

if __name__ == "__main__":
    try:
        run_simulation()
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the Backend! Make sure your FastAPI server is running on port 8000.")