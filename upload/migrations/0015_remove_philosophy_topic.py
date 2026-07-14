# Schema only — drops the now-unused philosophy_topic field; 0014 already moved every row's
# classification onto the generic Subcategory model.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0014_migrate_philosophy_topic'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='content',
            name='philosophy_topic',
        ),
    ]
