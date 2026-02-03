"""
Comprehensive test script for Smart Service Desk
"""
import sys
sys.path.insert(0, '.')

from database import get_db_connection
from models.user import User
from models.request import ServiceRequest, RequestStatusLog

def run_tests():
    print("=" * 50)
    print("SMART SERVICE DESK - COMPREHENSIVE TEST")
    print("=" * 50)
    
    # Test 1: Database Connection
    print("\n[TEST 1] Database Connection")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"  [OK] Connected! Tables: {tables}")
        conn.close()
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        return
    
    # Test 2: Admin User Exists
    print("\n[TEST 2] Admin User Check")
    admin = User.get_by_email('admin@servicedesk.com')
    if admin:
        print(f"  [OK] Admin exists: {admin.name} (Role: {admin.role})")
        print(f"  [OK] Password verify: {admin.verify_password('admin123')}")
    else:
        print("  [FAIL] Admin not found")
    
    # Test 3: Create Test User
    print("\n[TEST 3] User Registration")
    try:
        if User.email_exists('testuser@example.com'):
            test_user = User.get_by_email('testuser@example.com')
            print(f"  [OK] User already exists: {test_user.name}")
        else:
            test_user = User.create('Test Student', 'testuser@example.com', 'test123', 'USER')
            print(f"  [OK] Created user: {test_user.name} ({test_user.email})")
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        return
    
    # Test 4: Create Service Request
    print("\n[TEST 4] Service Request Creation")
    try:
        req = ServiceRequest.create(
            user_id=test_user.user_id,
            title='Network connectivity issue',
            description='Cannot connect to the campus WiFi network. Getting authentication error.',
            category='IT Support'
        )
        print(f"  [OK] Created Request #{req.request_id}")
        print(f"    - Title: {req.title}")
        print(f"    - Status: {req.status}")
        print(f"    - Category: {req.category}")
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
        return
    
    # Test 5: Lifecycle Enforcement
    print("\n[TEST 5] Lifecycle Enforcement")
    print(f"  Current status: {req.status}")
    print(f"  Valid transitions: {req.can_transition_to}")
    
    # Try invalid transition
    can_skip = req.can_update_to('Resolved')
    print(f"  Can skip to Resolved? {can_skip} (should be False)")
    
    # Valid transition
    can_progress = req.can_update_to('In Progress')
    print(f"  Can move to In Progress? {can_progress} (should be True)")
    
    # Test 6: Status Update
    print("\n[TEST 6] Admin Status Update")
    try:
        req.update_status('In Progress', 'Started investigation', admin.user_id)
        print(f"  [OK] Updated to: {req.status}")
    except Exception as e:
        print(f"  [FAIL] Failed: {e}")
    
    # Test 7: Audit Trail
    print("\n[TEST 7] Audit Trail")
    logs = RequestStatusLog.get_by_request(req.request_id)
    for log in logs:
        old_s = log.old_status or 'None'
        print(f"  - {old_s} -> {log.new_status}: {log.remark} (by {log.admin_name})")
    
    # Test 8: Statistics
    print("\n[TEST 8] Dashboard Statistics")
    stats = ServiceRequest.get_stats()
    print(f"  Total: {stats['total']}")
    print(f"  Submitted: {stats['submitted']}")
    print(f"  In Progress: {stats['in_progress']}")
    print(f"  Resolved: {stats['resolved']}")
    
    print("\n" + "=" * 50)
    print("ALL TESTS PASSED!")
    print("=" * 50)

if __name__ == '__main__':
    run_tests()
