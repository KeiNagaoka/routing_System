# Generated by Django 4.1.7 on 2024-10-20 16:00

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('routing', '0011_tag'),
    ]

    operations = [
        migrations.AddField(
            model_name='mapdata',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='mapdata',
            name='distance',
            field=models.IntegerField(default=1000),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='mapdata',
            name='time',
            field=models.IntegerField(default=13),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='mapdata',
            name='html',
            field=models.TextField(blank=True, null=True),
        ),
    ]
