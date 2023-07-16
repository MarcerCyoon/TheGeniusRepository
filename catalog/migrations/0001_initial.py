# Generated by Django 4.2.3 on 2023-07-16 03:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Designer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('desc', models.CharField(max_length=500)),
            ],
        ),
        migrations.CreateModel(
            name='MatchType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Enter a tag (e.g. 'social deduction' or 'bidding game')", max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='ORG',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('size', models.IntegerField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('main_host', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='catalog.designer')),
            ],
            options={
                'ordering': ['start_date'],
            },
        ),
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('summary', models.TextField(max_length=2000)),
                ('rules', models.TextField(help_text='Enter the rules of the Match here.', max_length=20000)),
                ('match_type', models.CharField(blank=True, choices=[('MM', 'Main Match'), ('DM', 'Death Match'), ('FM', 'Final Match')], max_length=2)),
                ('num_players', models.IntegerField()),
                ('ORG', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='catalog.org')),
                ('designer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='catalog.designer')),
                ('tags', models.ManyToManyField(help_text='Choose tags for this book', to='catalog.tag')),
            ],
        ),
    ]
