# RunPython only (no schema changes) — moves existing philosophy_topic values onto the new
# generic Subcategory model before 0015 drops the old field, so no classification is lost.

from django.db import migrations

TOPIC_LABELS = {
    'epistemology': 'Epistemology',
    'political_philosophy': 'Political Philosophy',
}


def migrate_forward(apps, schema_editor):
    Content = apps.get_model('upload', 'Content')
    Subcategory = apps.get_model('upload', 'Subcategory')

    for content in Content.objects.exclude(philosophy_topic__isnull=True).exclude(philosophy_topic=''):
        subcategory, _ = Subcategory.objects.get_or_create(
            parent_category='philosophy',
            slug=content.philosophy_topic,
            defaults={'name': TOPIC_LABELS.get(content.philosophy_topic, content.philosophy_topic)},
        )
        content.subcategory = subcategory
        content.save(update_fields=['subcategory'])


def migrate_backward(apps, schema_editor):
    Content = apps.get_model('upload', 'Content')
    for content in Content.objects.filter(subcategory__parent_category='philosophy'):
        content.philosophy_topic = content.subcategory.slug
        content.save(update_fields=['philosophy_topic'])


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0013_content_subcategory'),
    ]

    operations = [
        migrations.RunPython(migrate_forward, migrate_backward),
    ]
