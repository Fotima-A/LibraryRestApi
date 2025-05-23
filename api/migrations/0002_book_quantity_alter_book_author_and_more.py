# Generated by Django 4.2.16 on 2025-05-22 19:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='quantity',
            field=models.IntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='book',
            name='author',
            field=models.CharField(default='Unknown Author', max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='book',
            name='daily_price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AlterField(
            model_name='book',
            name='title',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('booked', 'BOOKED'), ('taken', 'TAKEN'), ('returned', 'RETURNED')], default='booked', max_length=20),
        ),
    ]
