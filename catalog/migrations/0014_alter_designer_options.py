# Generated by Django 4.2.3 on 2023-07-18 23:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0013_remove_match_designer_alter_match_designers'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='designer',
            options={'verbose_name': 'Designer', 'verbose_name_plural': 'Designers'},
        ),
    ]
