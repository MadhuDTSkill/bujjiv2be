# Generated by Django 5.2 on 2025-04-22 13:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chats_app', '0010_remove_conversation_attachments_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='attachments',
        ),
    ]
