# Generated by Django 5.1.2 on 2025-02-28 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0031_alter_order_payment_status_alter_order_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='status',
            field=models.CharField(default='Pending', max_length=50),
        ),
    ]
