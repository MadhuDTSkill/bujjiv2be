# Generated by Django 5.2 on 2025-04-22 11:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chats_app', '0008_rename_temp_documents_file_documents'),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='vector_ids',
            field=models.JSONField(blank=True, default=list),
        ),
    ]
