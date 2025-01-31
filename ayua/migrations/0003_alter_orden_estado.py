# Generated by Django 5.1.1 on 2024-12-01 05:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ayua', '0002_remove_pedido_motivo_rechazo_alter_pedido_estado_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orden',
            name='estado',
            field=models.CharField(choices=[('PENDIENTE', 'Pendiente'), ('CONFIRMADO', 'Confirmado'), ('FINALIZADO', 'Pagado'), ('RECHAZADO', 'Cancelado')], default='PENDIENTE', max_length=20),
        ),
    ]
