# Generated manually

from django.db import migrations, models


def recalculate_job_counts(apps, schema_editor):
    """Пересчитать количество работ для каждой категории"""
    Category = apps.get_model('core', 'Category')
    Order = apps.get_model('core', 'Order')
    
    for category in Category.objects.all():
        job_count = Order.objects.filter(category=category).count()
        category.job_count = job_count
        category.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_category_job_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='job_count',
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(recalculate_job_counts, migrations.RunPython.noop),
    ]
