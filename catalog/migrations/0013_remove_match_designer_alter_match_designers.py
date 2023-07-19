# Generated by Django 4.2.3 on 2023-07-18 23:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0012_auto_20230718_1946'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='match',
            name='designer',
        ),
        migrations.AlterField(
            model_name='match',
            name='designers',
            field=models.ManyToManyField(to='catalog.designer', verbose_name='Designer(s)'),
        ),
    ]