from django.core.management.base import BaseCommand
from emr.models import SyncOutbox
from emr.tasks import process_sync_outbox
from django.utils import timezone

class Command(BaseCommand):
    help = 'Retry failed Outbox sync tasks'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('[START] Retrying failed outbox tasks...'))

        # Find failed tasks (optionally filter by retry_count)
        failed_tasks = SyncOutbox.objects.filter(status='failed')
        
        count = failed_tasks.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS('[OK] No failed tasks found.'))
            return

        self.stdout.write(f'Found {count} failed tasks.')

        for outbox in failed_tasks:
            self.stdout.write(f' - Retrying Task {outbox.outbox_id} (Target: {outbox.target_system})')
            
            # Reset status to pending to be picked up by worker or immediate trigger
            # We trigger immediately via Celery
            outbox.status = 'pending'
            outbox.save(update_fields=['status'])
            
            process_sync_outbox.delay(str(outbox.outbox_id))

        self.stdout.write(self.style.SUCCESS(f'[DONE] Triggered retry for {count} tasks.'))
