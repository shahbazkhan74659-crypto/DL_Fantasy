# Schema only — adds the new nullable FK column. philosophy_topic (old data) is migrated into it
# by 0014, then removed by 0015 — kept as separate migrations so a MySQL DDL step never shares a
# migration with the RunPython data move (DDL isn't transactional; RunPython-only steps are).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0012_subcategory'),
    ]

    operations = [
        migrations.AddField(
            model_name='content',
            name='subcategory',
            field=models.ForeignKey(blank=True, help_text='Which Fiction story / Philosophy topic / Mythology tradition. Not used for God Valley.', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='contents', to='upload.subcategory'),
        ),
    ]
