import os
import sys
import django

# Setup Django Environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cdss_backend.settings')
django.setup()

from emr.models import Encounter, Order
from acct.models import User
from django.db.models import Count

def check_integrity():
    print("="*60)
    print("FK Integrity Check: CharField -> UUID ForeignKey")
    print("="*60)

    # 1. Check Encounter.doctor_id
    print("\n[1] Checking Encounter.doctor_id...")
    encounters = Encounter.objects.all()
    total_enc = encounters.count()
    users = set(str(u.user_id) for u in User.objects.all())
    
    orphans_enc = []
    for enc in encounters:
        if enc.doctor_id and enc.doctor_id not in users:
            orphans_enc.append(enc.doctor_id)
    
    print(f"    - Total Encounters: {total_enc}")
    print(f"    - Orphan doctor_ids: {len(orphans_enc)}")
    if orphans_enc:
        print(f"      Examples: {orphans_enc[:5]}")

    # 2. Check Order.ordered_by
    print("\n[2] Checking Order.ordered_by...")
    orders = Order.objects.all()
    total_ord = orders.count()
    
    orphans_ord = []
    for ord in orders:
        if ord.ordered_by and str(ord.ordered_by) not in users: # ordered_by might already be a user instance if accidentally FK? No, currently Char in model def check needed, assuming CharField as per plan
             orphans_ord.append(ord.ordered_by)

    print(f"    - Total Orders: {total_ord}")
    print(f"    - Orphan ordered_by IDs: {len(orphans_ord)}")
    if orphans_ord:
        print(f"      Examples: {orphans_ord[:5]}")

    # 3. Validation Result
    print("\n" + "="*60)
    if not orphans_enc and not orphans_ord:
        print("✅ INTEGRITY CHECK PASSED. Ready for migration.")
    else:
        print("❌ INTEGRITY CHECK FAILED. Found orphan records.")
        print("   Strategy needed: (a) Create dummy user, (b) Nullify, or (c) Delete.")
    print("="*60)

if __name__ == '__main__':
    check_integrity()
