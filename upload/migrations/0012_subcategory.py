# Schema only — creates the Subcategory table. See 0013/0014/0015 for how Content is wired to it.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('upload', '0011_content_philosophy_topic'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subcategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parent_category', models.CharField(choices=[('fiction', 'Fiction'), ('philosophy', 'Philosophy'), ('mythology', 'Mythology'), ('godvalley', 'The God Valley')], max_length=20)),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(max_length=100)),
            ],
            options={
                'ordering': ['name'],
                'constraints': [models.UniqueConstraint(fields=('parent_category', 'slug'), name='unique_subcategory_slug_per_parent')],
            },
        ),
    ]
