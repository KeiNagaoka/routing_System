# Generated by Django 4.1.7 on 2024-10-02 10:08

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('routing', '0006_addedtag'),
    ]

    operations = [
        migrations.RenameField(
            model_name='spot',
            old_name='langitude',
            new_name='latitude',
        ),
        migrations.RemoveField(
            model_name='spot',
            name='categories',
        ),
        migrations.RemoveField(
            model_name='spot',
            name='id',
        ),
        migrations.RemoveField(
            model_name='spot',
            name='posted_data',
        ),
        migrations.AddField(
            model_name='spot',
            name='hp',
            field=models.TextField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='spot',
            name='idx',
            field=models.AutoField(default=0, primary_key=True, serialize=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='addedtag',
            name='tag',
            field=models.TextField(),
        ),
        migrations.RemoveField(
            model_name='spot',
            name='tags',
        ),
        migrations.DeleteModel(
            name='Tag',
        ),
        migrations.AddField(
            model_name='spot',
            name='tags',
            field=models.TextField(default=[]),
            preserve_default=False,
        ),
    ]
