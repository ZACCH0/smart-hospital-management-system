"""Portable backup of the database plus uploaded media.

Works on SQLite, local Postgres and Render/Neon alike because it uses
Django's own serialiser instead of pg_dump. Restore with `loaddata`.
"""
import zipfile
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone


EXCLUDED_APPS = [
    'contenttypes',
    'auth.permission',
    'admin.logentry',
    'sessions',
]


class Command(BaseCommand):
    help = 'Write a timestamped zip containing database.json and media/.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            default=None,
            help='Directory for the archive (default: <BASE_DIR>/backups).',
        )
        parser.add_argument(
            '--keep',
            type=int,
            default=7,
            help='How many recent archives to retain (default: 7, 0 = keep all).',
        )

    def handle(self, *args, **options):
        output_dir = Path(options['output_dir'] or Path(settings.BASE_DIR) / 'backups')
        output_dir.mkdir(parents=True, exist_ok=True)

        stamp = timezone.now().strftime('%Y%m%d-%H%M%S-%f')
        archive_path = output_dir / f'shms-backup-{stamp}.zip'

        payload = StringIO()
        call_command(
            'dumpdata',
            *[f'--exclude={app}' for app in EXCLUDED_APPS],
            '--natural-foreign',
            '--natural-primary',
            '--indent=2',
            stdout=payload,
        )

        media_root = Path(settings.MEDIA_ROOT)
        media_files = 0
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('database.json', payload.getvalue())
            if media_root.exists():
                for path in media_root.rglob('*'):
                    if path.is_file():
                        archive.write(path, f'media/{path.relative_to(media_root).as_posix()}')
                        media_files += 1
            archive.writestr(
                'MANIFEST.txt',
                (
                    f'SHMS backup created {timezone.now().isoformat()}\n'
                    f'Database rows included in database.json\n'
                    f'Media files: {media_files}\n'
                    'Restore: python manage.py loaddata database.json\n'
                ),
            )

        keep = options['keep']
        removed = 0
        if keep and keep > 0:
            archives = sorted(output_dir.glob('shms-backup-*.zip'))
            for old in archives[:-keep]:
                old.unlink()
                removed += 1

        size_mb = archive_path.stat().st_size / (1024 * 1024)
        self.stdout.write(self.style.SUCCESS(
            f'Backup written to {archive_path} ({size_mb:.2f} MB, '
            f'{media_files} media file(s)).'
        ))
        if removed:
            self.stdout.write(f'Pruned {removed} old archive(s), keeping {keep}.')
