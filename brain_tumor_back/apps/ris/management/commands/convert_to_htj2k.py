
from django.core.management.base import BaseCommand
from ris.models import RadiologyStudy
from ris.clients.orthanc_client import OrthancClient
from ris.utils.dicom_converter import HTJ2KConverter
import pydicom
import io
import os
import tempfile
import requests

class Command(BaseCommand):
    help = 'Convert existing DICOM studies to HTJ2K format'

    def add_arguments(self, parser):
        parser.add_argument('--study', type=str, help='Study Instance UID to convert')
        parser.add_argument('--all', action='store_true', help='Convert all studies')
        parser.add_argument('--dry-run', action='store_true', help='Simulate conversion')

    def handle(self, *args, **options):
        client = OrthancClient()
        
        if options['study']:
            studies = RadiologyStudy.objects.filter(study_instance_uid=options['study'])
        elif options['all']:
            studies = RadiologyStudy.objects.all()
        else:
            self.stdout.write(self.style.ERROR("Please specify --study or --all"))
            return

        total = studies.count()
        self.stdout.write(f"Found {total} studies to process")
        
        for idx, study in enumerate(studies, 1):
            self.stdout.write(f"[{idx}/{total}] Processing Study: {study.study_instance_uid}")
            
            # Get Orthanc Study ID (Internal ID)
            # We might need to search it if not stored directly, but RadiologyStudy usually stores it?
            # Model has 'orthanc_study_id'
            orthanc_id = study.orthanc_study_id
            if not orthanc_id:
                self.stdout.write(self.style.WARNING(f"Skipping {study.study_instance_uid}: No Orthanc ID"))
                continue
            
            # Get Instances
            instances = client.get_study_instances(orthanc_id)
            if not instances:
                 self.stdout.write(self.style.WARNING(f"No instances found for {study.study_instance_uid}"))
                 continue
                 
            for instance_id in instances:
                try:
                    # 1. Download
                    dicom_bytes = client.download_dicom_instance(instance_id)
                    
                    # 2. Check Transfer Syntax
                    with io.BytesIO(dicom_bytes) as f:
                        ds = pydicom.dcmread(f)
                        
                    if HTJ2KConverter.is_htj2k(ds):
                        self.stdout.write(f"  Instance {instance_id} is already HTJ2K. Skipping.")
                        continue
                        
                    if options['dry_run']:
                        self.stdout.write(f"  [Dry Run] Would convert Instance {instance_id} ({ds.file_meta.TransferSyntaxUID})")
                        continue
                        
                    # 3. Convert
                    self.stdout.write(f"  Converting Instance {instance_id}...")
                    converted_ds = HTJ2KConverter.convert_dataset(ds)
                    
                    # 4. Upload as NEW instance
                    # Orthanc API: POST /instances via requests
                    with tempfile.NamedTemporaryFile(suffix='.dcm', delete=False) as tmp:
                         converted_ds.save_as(tmp.name)
                         tmp_path = tmp.name
                         
                    with open(tmp_path, 'rb') as f:
                        resp = requests.post(
                            f"{client.base_url}/instances",
                            data=f.read(), # Body is raw file
                            auth=client.auth
                        )
                    
                    if resp.status_code == 200:
                         new_id = resp.json().get('ID')
                         self.stdout.write(self.style.SUCCESS(f"  Uploaded new instance {new_id}"))
                         
                         # 5. Delete OLD instance ??
                         # User asked to "Store as HTJ2K" and "Match default to HTJ2K"
                         # Deleting old ensures we use HTJ2K. Use cascading delete in Orthanc if needed.
                         # Deleting Instance: DELETE /instances/{id}
                         del_resp = requests.delete(f"{client.base_url}/instances/{instance_id}", auth=client.auth)
                         if del_resp.status_code == 200:
                             self.stdout.write(f"  Deleted old instance {instance_id}")
                         else:
                             self.stdout.write(self.style.WARNING(f"  Failed to delete old instance {instance_id}"))
                             
                    else:
                        self.stdout.write(self.style.ERROR(f"  Failed to upload converted instance: {resp.text}"))
                        
                    os.unlink(tmp_path)
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Error processing instance {instance_id}: {e}"))
            
            self.stdout.write(self.style.SUCCESS(f"Study {study.study_instance_uid} processing complete"))
