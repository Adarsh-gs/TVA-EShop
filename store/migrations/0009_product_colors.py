# Generated by Django 5.1.2 on 2025-01-04 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0008_coupon_cart'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='colors',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
