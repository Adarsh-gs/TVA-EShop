# Generated by Django 5.1.2 on 2025-02-28 16:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0036_remove_orderitem_status_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='status',
            field=models.CharField(default='Pending', max_length=50),
        ),
    ]
