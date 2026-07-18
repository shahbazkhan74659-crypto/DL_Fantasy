from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Collection, CollectionItem, Content


class CollectionUploadViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.staff = User.objects.create_user(username='dex', password='pw', is_staff=True)
        cls.essay = Content.objects.create(category='philosophy', title='Essay', slug='essay', body='b')
        cls.chapter = Content.objects.create(category='godvalley', title='Opening', slug='opening', chapter_number=1, body='b')

    def setUp(self):
        self.client.force_login(self.staff)

    def test_upload_collections_page_ok(self):
        response = self.client.get(reverse('upload_collections'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'upload_collection_form.html')

    def test_create_collection_with_items(self):
        response = self.client.post(reverse('upload_collections'), {
            'title': 'Best Of',
            'description': 'd',
            'items': [self.essay.pk, self.chapter.pk],
        })
        self.assertRedirects(response, reverse('upload_collections'))
        collection = Collection.objects.get(title='Best Of')
        # 'is_published' absent from the POST = unchecked box = saved as a draft.
        self.assertFalse(collection.is_published)
        self.assertEqual(collection.items.count(), 2)
        # Picker display order: God Valley group renders before Philosophy, so the chapter
        # gets position 1.
        self.assertEqual(list(collection.items.values_list('content_id', flat=True)), [self.chapter.pk, self.essay.pk])

    def test_edit_collection_page_ok(self):
        collection = Collection.objects.create(title='Anthology')
        CollectionItem.objects.create(collection=collection, content=self.essay, position=1)
        response = self.client.get(reverse('edit_collection', args=[collection.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'upload_collection_edit.html')

    def test_move_collection_item_swaps_positions(self):
        collection = Collection.objects.create(title='Anthology')
        first = CollectionItem.objects.create(collection=collection, content=self.essay, position=1)
        second = CollectionItem.objects.create(collection=collection, content=self.chapter, position=2)
        response = self.client.post(reverse('move_collection_item', args=[second.pk]), {'direction': 'up'})
        self.assertRedirects(response, reverse('edit_collection', args=[collection.pk]))
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual((second.position, first.position), (1, 2))

    def test_non_staff_404s(self):
        User = get_user_model()
        visitor = User.objects.create_user(username='visitor', password='pw')
        self.client.force_login(visitor)
        response = self.client.get(reverse('upload_collections'))
        self.assertEqual(response.status_code, 404)
