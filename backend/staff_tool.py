import requests
import time
import os

BASE_URL = "http://localhost:8000/api"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    while True:
        clear_screen()
        print("="*40)
        print("   PUC BOOKSTORE STAFF TERMINAL")
        print("="*40)
        print("\nReady to verify student pickups.")
        
        pin = input("\nEnter Student's 6-digit PIN (or 'q' to quit): ").strip()
        
        if pin.lower() == 'q':
            break
            
        if len(pin) != 6:
            print("\n[ERROR] PIN must be exactly 6 digits.")
            time.sleep(2)
            continue

        print(f"\nVerifying PIN {pin}...")
        
        try:
            # Step 1: Lookup PIN to get order details
            response = requests.get(f"{BASE_URL}/admin/orders/lookup/{pin}")
            
            if response.status_code == 200:
                order = response.json()
                print("\n" + "*"*40)
                print("   SUCCESS: ORDER VERIFIED!")
                print(f"   Customer: {order['customer_name']}")
                print(f"   Total: ${order['total_amount']}")
                print(f"   Location: {order['prepared_location']}")
                print("*"*40)
                
                confirm = input("\nRelease books to student? (y/n): ").strip().lower()
                if confirm == 'y':
                    # Step 2: Fulfill pickup (Using system staff ID 1 as default for terminal)
                    f_res = requests.patch(f"{BASE_URL}/admin/orders/{order['order_id']}/pickup/?staff_id=1")
                    if f_res.status_code == 200:
                        print("\n[SUCCESS] Order marked as Picked Up.")
                    else:
                        print(f"\n[ERROR] Could not release: {f_res.json().get('detail')}")
            else:
                data = response.json()
                print(f"\n[FAILED] {data.get('detail', 'Invalid PIN')}")
        
        except requests.RequestException as e:
            print(f"\n[CONNECTION ERROR] Is the backend running? {e}")
            
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
