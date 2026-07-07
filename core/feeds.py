from django.contrib.syndication.views import Feed
from django.urls import reverse

from upload.models import Content


class LatestContentFeed(Feed):
    title = "DL Fantasy — Latest"
    link = "/"
    description = "New writings and God Valley chapters from DL Fantasy."

    def items(self):
        return Content.objects.filter(is_published=True).order_by('-created_at')[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt or item.body[:300]

    def item_link(self, item):
        if item.category == Content.Category.GODVALLEY:
            return reverse('godvalley_detail', args=[item.slug])
        return reverse('writings_detail', args=[item.category, item.slug])

    def item_pubdate(self, item):
        return item.created_at
