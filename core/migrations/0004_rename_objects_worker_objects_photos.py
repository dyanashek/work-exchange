# Generated by Django 4.2 on 2024-08-16 08:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_remove_worker_profile_complete_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='worker',
            old_name='objects',
            new_name='objects_photos',
        ),
    ]
