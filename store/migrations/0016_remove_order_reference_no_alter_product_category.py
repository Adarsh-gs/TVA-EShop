# Generated by Django 5.1.2 on 2025-01-13 05:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0015_order_payment_status_order_reference_no'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='reference_no',
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='store.category'),
        ),
    ]
