# Generated by Django 5.1.2 on 2024-11-05 06:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('routing', '0012_mapdata_created_at_mapdata_distance_mapdata_time_and_more'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='node',
            table='routing_node',
        ),
        migrations.AlterModelTable(
            name='spot',
            table='routing_spot',
        ),
    ]
