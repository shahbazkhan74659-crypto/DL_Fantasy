from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from upload.models import Content


class ContentSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Content.objects.filter(is_published=True).order_by('-created_at')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "monthly"

    def items(self):
        return ['home', 'writings', 'godvalley_list', 'godvalley_chapters', 'archive', 'about', 'news']

    def location(self, item):
        return reverse(item)
