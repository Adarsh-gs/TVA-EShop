# Generated by Django 5.1.2 on 2025-01-19 14:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0026_order_discount_order_payment_method_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='razorpay_order_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
