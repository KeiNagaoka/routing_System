# Generated by Django 4.1.7 on 2024-10-20 04:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('routing', '0008_mapdata'),
    ]

    operations = [
        migrations.CreateModel(
            name='Node',
            fields=[
                ('idx', models.AutoField(primary_key=True, serialize=False)),
                ('node', models.IntegerField(unique=True)),
                ('name', models.TextField()),
                ('lat', models.FloatField()),
                ('lon', models.FloatField()),
                ('tags', models.TextField()),
            ],
        ),
        migrations.RenameField(
            model_name='spot',
            old_name='latitude',
            new_name='lat',
        ),
        migrations.RenameField(
            model_name='spot',
            old_name='longitude',
            new_name='lon',
        ),
        migrations.AlterField(
            model_name='spot',
            name='name',
            field=models.CharField(max_length=64, unique=True),
        ),
    ]
