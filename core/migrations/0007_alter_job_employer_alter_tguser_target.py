# Generated by Django 4.2 on 2024-08-17 05:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_channelforemployers_channelforworkers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='employer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='jobs', to='core.employer', verbose_name='Работодатель'),
        ),
        migrations.AlterField(
            model_name='tguser',
            name='target',
            field=models.CharField(choices=[('1', 'Работник'), ('2', 'Работодатель')], max_length=10, verbose_name='Тип пользователя'),
        ),
    ]
