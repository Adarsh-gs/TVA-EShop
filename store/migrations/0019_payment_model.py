# Generated by Django 5.1.2 on 2025-01-15 10:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0018_cart_selected_color_cart_selected_size'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment_model',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('amount', models.CharField(max_length=100)),
                ('order_id', models.CharField(blank=True, max_length=100)),
                ('razorpay_payment_id', models.CharField(blank=True, max_length=100)),
                ('paid', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'store_payment_model',
            },
        ),
    ]
