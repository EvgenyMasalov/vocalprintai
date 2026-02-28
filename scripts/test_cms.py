import requests
import uuid

BASE_URL = "http://localhost:8500"
ADMIN_SECRET = "vocalprint_admin_2024"

def test_admin_flow():
    username = f"admin_{uuid.uuid4().hex[:6]}"
    email = f"{username}@test.com"
    password = "adminpassword"

    print(f"Testing admin registration for {username}...")
    
    # 1. Register as admin
    reg_response = requests.post(f"{BASE_URL}/register", json={
        "username": username,
        "email": email,
        "password": password,
        "admin_secret": ADMIN_SECRET
    })
    
    if reg_response.status_code != 200:
        print(f"Registration failed: {reg_response.text}")
        return

    user_data = reg_response.json()
    print(f"Admin registered: {user_data.get('username')}, is_admin: {user_data.get('is_admin')}")

    # 2. Login
    login_response = requests.post(f"{BASE_URL}/token", data={
        "username": username,
        "password": password
    })
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return
        
    login_data = login_response.json()
    print(f"Login success, is_admin: {login_data.get('is_admin')}")
    token = login_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Test Admin Clients endpoint
    clients_res = requests.get(f"{BASE_URL}/admin/clients", headers=headers)
    print(f"Admin Clients status: {clients_res.status_code}, count: {len(clients_res.json())}")

    # 4. Test Admin Generations endpoint
    gens_res = requests.get(f"{BASE_URL}/admin/generations", headers=headers)
    print(f"Admin Generations status: {gens_res.status_code}, count: {len(gens_res.json())}")

if __name__ == "__main__":
    try:
        test_admin_flow()
    except Exception as e:
        print(f"Error: {e}")
