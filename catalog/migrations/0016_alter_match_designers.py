# Generated by Django 4.2.3 on 2023-07-18 23:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0015_alter_designer_options_alter_match_designers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='designers',
            field=models.ManyToManyField(to='catalog.designer', verbose_name='Designer(s)'),
        ),
    ]
