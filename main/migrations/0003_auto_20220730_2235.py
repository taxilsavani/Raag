# Generated by Django 3.0.7 on 2022-07-31 02:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_recommended_song'),
    ]

    operations = [
        migrations.AddField(
            model_name='recommended_song',
            name='song_albumsrc',
            field=models.CharField(default=1, max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='recommended_song',
            name='song_channel',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='recommended_song',
            name='song_dur',
            field=models.CharField(default=1, max_length=7),
            preserve_default=False,
        ),
    ]