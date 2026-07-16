from django.contrib.syndication.views import Feed

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
        return item.get_absolute_url()

    def item_pubdate(self, item):
        return item.created_at
