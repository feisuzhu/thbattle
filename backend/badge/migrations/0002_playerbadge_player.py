# Generated by Django 3.2.13 on 2022-06-02 15:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('badge', '0001_initial'),
        ('player', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='playerbadge',
            name='player',
            field=models.ForeignKey(help_text='玩家', on_delete=django.db.models.deletion.CASCADE, related_name='+', to='player.player'),
        ),
    ]
