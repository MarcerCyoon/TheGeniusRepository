# Generated by Django 4.2.15 on 2024-09-09 04:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0022_alter_match_rules'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='yearaward',
            options={'ordering': ['year', 'award']},
        ),
    ]
