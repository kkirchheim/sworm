# Generated by Django 3.2.3 on 2021-05-23 19:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sworm', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=250)),
                ('abstract', models.TextField(max_length=2000)),
                ('publish_on', models.DateField()),
            ],
        ),
        migrations.AddField(
            model_name='customuser',
            name='articles',
            field=models.ManyToManyField(related_name='marked_articles', to='sworm.Article'),
        ),
    ]
