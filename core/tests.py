from django.test import TestCase
from django.urls import reverse

from upload.models import Content

PAGE_SIZE = 12


class HomeViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Content.objects.create(category='fiction', title='Published', slug='published', body='b')
        Content.objects.create(category='fiction', title='Unpublished', slug='unpublished', body='b', is_published=False)

    def test_home_ok(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_home_excludes_unpublished(self):
        response = self.client.get(reverse('home'))
        titles = [entry.title for entry in response.context['entries']]
        self.assertIn('Published', titles)
        self.assertNotIn('Unpublished', titles)


class WritingsViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Content.objects.create(category='fiction', title='Fiction Old', slug='fiction-old', excerpt='old excerpt', body='b')
        Content.objects.create(category='fiction', title='Fiction New', slug='fiction-new', excerpt='new excerpt', body='b')
        Content.objects.create(category='philosophy', title='Philosophy Piece', slug='philosophy-piece', body='b')
        Content.objects.create(category='fiction', title='Fiction Draft', slug='fiction-draft', body='b', is_published=False)

    def test_writings_ok(self):
        response = self.client.get(reverse('writings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'writings.html')

    def test_writings_highlight_is_most_recent_per_category(self):
        response = self.client.get(reverse('writings'))
        highlights = response.context['highlights']
        self.assertEqual(highlights['fiction'].slug, 'fiction-new')
        self.assertEqual(highlights['philosophy'].slug, 'philosophy-piece')
        self.assertIsNone(highlights['mythology'])

    def test_writings_category_list_ok(self):
        response = self.client.get(reverse('writings_category_list', args=['fiction']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'writings_list.html')

    def test_writings_category_list_invalid_category_404s(self):
        response = self.client.get(reverse('writings_category_list', args=['nonsense']))
        self.assertEqual(response.status_code, 404)

    def test_writings_category_list_excludes_unpublished(self):
        response = self.client.get(reverse('writings_category_list', args=['fiction']))
        slugs = [entry.slug for entry in response.context['entries']]
        self.assertNotIn('fiction-draft', slugs)

    def test_writings_category_list_paginates(self):
        for i in range(PAGE_SIZE + 3):
            Content.objects.create(category='mythology', title=f'Myth {i}', slug=f'myth-{i}', body='b')
        response = self.client.get(reverse('writings_category_list', args=['mythology']))
        self.assertEqual(len(response.context['entries']), PAGE_SIZE)
        response_page2 = self.client.get(reverse('writings_category_list', args=['mythology']), {'page': 2})
        self.assertEqual(len(response_page2.context['entries']), 3)

    def test_writings_detail_ok(self):
        response = self.client.get(reverse('writings_detail', args=['fiction', 'fiction-new']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'writings_detail.html')

    def test_writings_detail_404_for_unpublished(self):
        response = self.client.get(reverse('writings_detail', args=['fiction', 'fiction-draft']))
        self.assertEqual(response.status_code, 404)

    def test_writings_detail_404_for_wrong_category(self):
        response = self.client.get(reverse('writings_detail', args=['philosophy', 'fiction-new']))
        self.assertEqual(response.status_code, 404)


class GodValleyViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ch1 = Content.objects.create(category='godvalley', title='Beginnings', slug='ch-1', chapter_number=1, body='b')
        cls.ch2 = Content.objects.create(category='godvalley', title='Middle', slug='ch-2', chapter_number=2, body='b')
        cls.ch3 = Content.objects.create(category='godvalley', title='End', slug='ch-3', chapter_number=3, body='b')
        Content.objects.create(category='godvalley', title='Draft Chapter', slug='ch-draft', chapter_number=4, body='b', is_published=False)

    def test_godvalley_list_ok(self):
        response = self.client.get(reverse('godvalley_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'godvalley_list.html')

    def test_godvalley_chapters_ok(self):
        response = self.client.get(reverse('godvalley_chapters'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'godvalley_chapters.html')

    def test_godvalley_chapters_search_filters_by_title(self):
        response = self.client.get(reverse('godvalley_chapters'), {'q': 'middle'})
        slugs = [chapter.slug for chapter in response.context['chapters']]
        self.assertEqual(slugs, ['ch-2'])

    def test_godvalley_chapters_paginates(self):
        for i in range(PAGE_SIZE + 2):
            Content.objects.create(category='godvalley', title=f'Filler {i}', slug=f'filler-{i}', chapter_number=100 + i, body='b')
        response = self.client.get(reverse('godvalley_chapters'))
        self.assertEqual(len(response.context['chapters']), PAGE_SIZE)

    def test_godvalley_detail_ok(self):
        response = self.client.get(reverse('godvalley_detail', args=['ch-2']))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'godvalley_detail.html')

    def test_godvalley_detail_prev_next_middle_chapter(self):
        response = self.client.get(reverse('godvalley_detail', args=['ch-2']))
        self.assertEqual(response.context['prev_chapter'].slug, 'ch-1')
        self.assertEqual(response.context['next_chapter'].slug, 'ch-3')

    def test_godvalley_detail_first_chapter_has_no_prev(self):
        response = self.client.get(reverse('godvalley_detail', args=['ch-1']))
        self.assertIsNone(response.context['prev_chapter'])
        self.assertEqual(response.context['next_chapter'].slug, 'ch-2')

    def test_godvalley_detail_last_chapter_has_no_next(self):
        response = self.client.get(reverse('godvalley_detail', args=['ch-3']))
        self.assertEqual(response.context['prev_chapter'].slug, 'ch-2')
        self.assertIsNone(response.context['next_chapter'])

    def test_godvalley_detail_404_for_unpublished(self):
        response = self.client.get(reverse('godvalley_detail', args=['ch-draft']))
        self.assertEqual(response.status_code, 404)


class StaticPageViewTests(TestCase):
    def test_archive_ok(self):
        response = self.client.get(reverse('archive'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'archive.html')

    def test_about_ok(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about.html')

    def test_concepts_ok(self):
        response = self.client.get(reverse('concepts'))
        self.assertEqual(response.status_code, 200)

    def test_collections_ok(self):
        response = self.client.get(reverse('collections'))
        self.assertEqual(response.status_code, 200)


class SearchViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Content.objects.create(category='fiction', title='Dragon Story', slug='dragon-story', body='b')
        Content.objects.create(category='godvalley', title='Dragon Chapter', slug='dragon-chapter', chapter_number=1, body='b')
        Content.objects.create(category='philosophy', title='Unrelated', slug='unrelated', body='b')
        Content.objects.create(category='fiction', title='Dragon Draft', slug='dragon-draft', body='b', is_published=False)

    def test_search_ok(self):
        response = self.client.get(reverse('search'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search.html')

    def test_search_no_query_returns_no_results(self):
        response = self.client.get(reverse('search'))
        self.assertEqual(len(response.context['results']), 0)

    def test_search_matches_title_across_categories(self):
        response = self.client.get(reverse('search'), {'q': 'dragon'})
        slugs = {entry.slug for entry in response.context['results']}
        self.assertEqual(slugs, {'dragon-story', 'dragon-chapter'})

    def test_search_excludes_unpublished(self):
        response = self.client.get(reverse('search'), {'q': 'dragon'})
        slugs = {entry.slug for entry in response.context['results']}
        self.assertNotIn('dragon-draft', slugs)


class FeedTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Content.objects.create(category='fiction', title='Fiction Item', slug='fiction-item', body='b')
        Content.objects.create(category='godvalley', title='GV Chapter', slug='gv-chapter', chapter_number=1, body='b')
        Content.objects.create(category='fiction', title='Draft Item', slug='draft-item', body='b', is_published=False)

    def test_feed_ok(self):
        response = self.client.get(reverse('feed'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/rss+xml; charset=utf-8')

    def test_feed_excludes_unpublished_and_links_correctly(self):
        response = self.client.get(reverse('feed'))
        content = response.content.decode()
        self.assertIn('/writings/fiction/fiction-item/', content)
        self.assertIn('/godvalley/gv-chapter/', content)
        self.assertNotIn('draft-item', content)


class SitemapTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Content.objects.create(category='fiction', title='Fiction Item', slug='fiction-item', body='b')
        Content.objects.create(category='fiction', title='Draft Item', slug='draft-item', body='b', is_published=False)

    def test_sitemap_ok(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)

    def test_sitemap_excludes_unpublished_and_placeholders(self):
        response = self.client.get('/sitemap.xml')
        content = response.content.decode()
        self.assertIn('/writings/fiction/fiction-item/', content)
        self.assertNotIn('draft-item', content)
        self.assertNotIn('/concepts/', content)
        self.assertNotIn('/collections/', content)
