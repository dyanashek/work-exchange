# Generated by Django 4.2 on 2024-09-16 03:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_employerreview_review_rus_workerreview_review_heb_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='employer',
            name='name',
            field=models.CharField(default='Company', max_length=150, verbose_name='Имя/название компании'),
        ),
    ]
