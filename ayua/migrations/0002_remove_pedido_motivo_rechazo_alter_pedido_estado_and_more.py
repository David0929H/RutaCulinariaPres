# Generated by Django 5.1.1 on 2024-12-01 04:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ayua', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pedido',
            name='motivo_rechazo',
        ),
        migrations.AlterField(
            model_name='pedido',
            name='estado',
            field=models.CharField(choices=[('pendiente', 'Pendiente'), ('pagado', 'Pagado')], default='pendiente', max_length=20),
        ),
        migrations.AlterField(
            model_name='pedido',
            name='total',
            field=models.DecimalField(decimal_places=0, max_digits=10),
        ),
    ]