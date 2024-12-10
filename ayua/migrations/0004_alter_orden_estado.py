# Generated by Django 5.1.1 on 2024-12-01 05:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ayua', '0003_alter_orden_estado'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orden',
            name='estado',
            field=models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('CONFIRMADO', 'Confirmado'), ('PAGADO', 'Pagado'), ('RECHAZADO', 'Cancelado')], default='PENDIENTE', max_length=20),
        ),
    ]