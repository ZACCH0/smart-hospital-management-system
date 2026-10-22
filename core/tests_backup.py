import json
import tempfile
import zipfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase, override_settings

from core.testing import make_user


class BackupCommandTests(TestCase):
    def test_archive_contains_database_and_media(self):
        user = make_user('admin', email='backup-check@example.com')
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            media = tmp_path / 'media'
            media.mkdir()
            (media / 'note.txt').write_text('scan', encoding='utf-8')

            output = tmp_path / 'out'
            with override_settings(MEDIA_ROOT=media):
                call_command('backup_data', output_dir=str(output), keep=0)

            archives = list(output.glob('shms-backup-*.zip'))
            self.assertEqual(len(archives), 1)

            with zipfile.ZipFile(archives[0]) as archive:
                names = archive.namelist()
                self.assertIn('database.json', names)
                self.assertIn('media/note.txt', names)
                self.assertIn('MANIFEST.txt', names)
                data = json.loads(archive.read('database.json'))

            emails = [
                row['fields']['email']
                for row in data
                if row['model'] == 'accounts.customuser'
            ]
            self.assertIn(user.email, emails)

    def test_old_archives_are_pruned(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output = tmp_path / 'out'
            media = tmp_path / 'media'
            media.mkdir()

            with override_settings(MEDIA_ROOT=media):
                call_command('backup_data', output_dir=str(output), keep=0)
                call_command('backup_data', output_dir=str(output), keep=1)

            self.assertEqual(len(list(output.glob('shms-backup-*.zip'))), 1)
