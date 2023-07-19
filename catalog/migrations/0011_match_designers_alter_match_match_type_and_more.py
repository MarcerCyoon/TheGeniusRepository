# Generated by Django 4.2.3 on 2023-07-18 23:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0010_alter_match_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='designers',
            field=models.ManyToManyField(related_name='designer', to='catalog.designer', verbose_name='Designer(s)'),
        ),
        migrations.AlterField(
            model_name='match',
            name='match_type',
            field=models.CharField(choices=[('DM', 'Death Match'), ('MM', 'Main Match')], max_length=2),
        ),
        migrations.AlterField(
            model_name='tag',
            name='name',
            field=models.CharField(help_text="Enter a tag (e.g. 'social deduction' or 'bidding')", max_length=200),
        ),
    ]
