# Generated by Django 2.1.7 on 2019-02-20 20:41

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('kf_main', '0005_remove_deck_creature_pwr'),
    ]

    operations = [
        migrations.AddField(
            model_name='deck',
            name='creature_pwr',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]