# Generated by Django 3.2.3 on 2021-05-24 12:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('sworm', '0004_auto_20210524_1137'),
    ]

    operations = [
        migrations.CreateModel(
            name='Journal',
            fields=[
                ('issn', models.CharField(max_length=250, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=250)),
            ],
        ),
        migrations.AlterField(
            model_name='article',
            name='id',
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='article',
            name='journal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='sworm.journal'),
        ),
    ]