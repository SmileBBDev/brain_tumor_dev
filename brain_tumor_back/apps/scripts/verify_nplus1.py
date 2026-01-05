import os
import sys
import django
from django.db import connection, reset_queries
import time

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cdss_backend.settings')
django.setup()

from emr.models import Encounter, Order, PatientCache
from acct.models import User
from emr.serializers import EncounterSerializer, OrderSerializer
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

def benchmark_endpoint(viewset_class, action, model_name):
    print(f"\n--- Benchmarking {model_name} List ---")
    
    factory = APIRequestFactory()
    request = factory.get('/')
    
    # 1. Warmup & Check Count
    count = viewset_class.queryset.model.objects.count()
    print(f"Total {model_name}s in DB: {count}")
    
    if count < 5:
        print("!! Not enough data to benchmark. Need at least 5 records.")
        return

    # 2. Reset Queries
    reset_queries()
    
    # 3. Serialize List (simulating list view)
    viewset = viewset_class()
    viewset.action = 'list' # Must set action manually for get_serializer_class
    viewset.request = request
    viewset.format_kwarg = None
    
    queryset = viewset.get_queryset()

    start_time = time.time()
    serializer_class = viewset.get_serializer_class()
    
    # We must instantiate serializer with context just in case
    serializer = serializer_class(queryset, many=True, context={'request': request})
    data = serializer.data # This triggers evaluation
    end_time = time.time()
    
    query_count = len(connection.queries)
    print(f"Fetched {count} items in {end_time - start_time:.4f}s")
    print(f"Total Queries: {query_count}")
    
    # Heuristic for N+1: If queries > count + 5, specific issue likely
    if query_count > (count / 2): # Very rough heuristic
        print(f"WARNING: High query count detected! Possible N+1. (Queries: {query_count}, Items: {count})")
        # Print unique queries to identify duplicated ones
        sql_signs = {}
        for q in connection.queries:
            sql = q['sql'].split('WHERE')[0] if 'WHERE' in q['sql'] else q['sql']
            sql_signs[sql] = sql_signs.get(sql, 0) + 1
        
        for sql, c in sql_signs.items():
            if c > 1:
                print(f"  Repeated {c} times: {sql[:100]}...")
    else:
        print("✅ Query count looks optimized.")

def main():
    # Detect ViewSets
    from emr.viewsets import EncounterViewSet, OrderViewSet
    
    # Ensure we have data
    if Encounter.objects.count() == 0:
        print("Creating dummy data for test...")
        # Create Dummy User & Patient
        u, _ = User.objects.get_or_create(username='testdoc', role='doctor', email='b@b.com')
        p, _ = PatientCache.objects.get_or_create(patient_id='P-BENCH', family_name='Test', given_name='Bench', gender='male', birth_date='2000-01-01')
        
        # Create 10 Encounters
        for i in range(10):
            Encounter.objects.create(
                encounter_id=f'E-TEST-{i}',
                patient=p,
                doctor=u,
                encounter_type='outpatient',
                encounter_date='2025-01-01 10:00:00',
                status='scheduled'
            )
    
    # Benchmark Encounter
    benchmark_endpoint(EncounterViewSet, 'list', 'Encounter')
    
    # Benchmark Order
    if Order.objects.count() == 0:
         # Create dummy orders
         u = User.objects.first()
         p = PatientCache.objects.first()
         enc = Encounter.objects.first()
         for i in range(10):
            Order.objects.create(
                order_id=f'O-TEST-{i}',
                patient=p,
                encounter=enc,
                ordered_by=u,
                order_type='medication',
                status='pending'
            )

    benchmark_endpoint(OrderViewSet, 'list', 'Order')

if __name__ == '__main__':
    main()
