# Generated by Django 5.1.2 on 2025-02-28 15:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0032_orderitem_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='status',
        ),
    ]
