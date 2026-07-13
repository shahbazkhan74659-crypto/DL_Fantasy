from django.db import migrations


def seed_news(apps, schema_editor):
    News = apps.get_model('upload', 'News')
    News.objects.get_or_create(
        slug='a-new-arc-begins-in-the-god-valley',
        defaults={
            'title': 'A New Arc Begins in The God Valley',
            'tag': 'announcement',
            'body': (
                "After months of quiet drafting, the next arc of The God Valley is underway — "
                "new chapters are being added to the archive as they're finished, continuing the "
                "story exactly where it left off.\n\n"
                "No release schedule, no previews: chapters go up the moment they're ready, the "
                "same way everything else on this site does."
            ),
        },
    )


def unseed_news(apps, schema_editor):
    News = apps.get_model('upload', 'News')
    News.objects.filter(slug='a-new-arc-begins-in-the-god-valley').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0005_news'),
    ]

    operations = [
        migrations.RunPython(seed_news, unseed_news),
    ]
