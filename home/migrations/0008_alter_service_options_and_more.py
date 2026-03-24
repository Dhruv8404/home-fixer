from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0007_servicemanprofile_live_lat_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='service',
            options={'ordering': ['-created_at']},
        ),
        migrations.RenameField(
            model_name='service',
            old_name='base_price',
            new_name='price',
        ),
        migrations.RemoveField(
            model_name='service',
            name='latitude',
        ),
        migrations.RemoveField(
            model_name='service',
            name='longitude',
        ),
        migrations.RemoveField(
            model_name='bookingitem',
            name='service',
        ),

        # ✅ ADD product FIRST before AlterUniqueTogether
        migrations.AddField(
            model_name='bookingitem',
            name='product',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to='home.product',
            ),
        ),
        migrations.AddField(
            model_name='bookingitem',
            name='is_approved',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='bookingitem',
            name='quantity',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='service',
            name='serviceman',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='services',
                to='home.servicemanprofile',
            ),
        ),

        # ✅ AlterUniqueTogether AFTER product field exists
        migrations.AlterUniqueTogether(
            name='bookingitem',
            unique_together={('booking', 'product')},
        ),

        migrations.AlterField(
            model_name='bookingitem',
            name='booking',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='items',
                to='home.booking',
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(
                limit_choices_to={'category_type': 'PRODUCT'},
                on_delete=django.db.models.deletion.PROTECT,
                to='home.category',
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='min_stock_alert',
            field=models.PositiveIntegerField(default=5),
        ),
        migrations.AlterField(
            model_name='product',
            name='stock_quantity',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='service',
            name='category',
            field=models.ForeignKey(
                limit_choices_to={'category_type': 'SERVICE'},
                on_delete=django.db.models.deletion.CASCADE,
                to='home.category',
            ),
        ),
        migrations.AddIndex(
            model_name='bookingitem',
            index=models.Index(fields=['booking'], name='home_bookin_booking_81e8e3_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['vendor'], name='home_produc_vendor__75daeb_idx'),
        ),
        migrations.AddIndex(
            model_name='product',
            index=models.Index(fields=['category'], name='home_produc_categor_cb7dec_idx'),
        ),
        migrations.AddIndex(
            model_name='service',
            index=models.Index(fields=['serviceman'], name='home_servic_service_3e27ea_idx'),
        ),
    ]