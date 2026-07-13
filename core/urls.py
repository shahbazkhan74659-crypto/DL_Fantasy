from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .feeds import LatestContentFeed
from .forms import StyledPasswordChangeForm

urlpatterns = [
    path('', views.home, name='home'),
    path('writings/', views.writings, name='writings'),
    path('writings/<slug:category>/', views.writings_category_list, name='writings_category_list'),
    path('writings/<slug:category>/<slug:slug>/', views.writings_detail, name='writings_detail'),
    path('godvalley/', views.godvalley_list, name='godvalley_list'),
    path('godvalley/chapters/', views.godvalley_chapters, name='godvalley_chapters'),
    path('godvalley/<slug:slug>/', views.godvalley_detail, name='godvalley_detail'),
    path('search/', views.search, name='search'),
    path('favourites/', views.favourites, name='favourites'),
    path('favourites/<int:content_id>/toggle/', views.toggle_favourite, name='toggle_favourite'),
    path('reading-list/', views.reading_list, name='reading_list'),
    path('reading-list/<int:content_id>/toggle/', views.toggle_reading_list_item, name='toggle_reading_list_item'),
    path('downloads/', views.downloads, name='downloads'),
    path('downloads/<int:content_id>/', views.download_content, name='download_content'),
    path('feed/', LatestContentFeed(), name='feed'),
    path('archive/', views.archive, name='archive'),
    path('concepts/', views.concepts, name='concepts'),
    path('collections/', views.collections, name='collections'),
    path('about/', views.about, name='about'),
    path('news/', views.news, name='news'),
    path('news/new/', views.create_news, name='create_news'),
    path('news/<slug:slug>/', views.news_detail, name='news_detail'),
    path('news/<slug:slug>/edit/', views.edit_news, name='edit_news'),
    path('news/<slug:slug>/delete/', views.delete_news, name='delete_news'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('login/google/', views.google_login, name='google_login'),
    path('login/google/callback/', views.google_callback, name='google_callback'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('account/', views.account, name='account'),
    path('profile/', views.profile, name='profile'),
    path('users/', views.users_list, name='users_list'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path(
        'account/password/',
        auth_views.PasswordChangeView.as_view(
            template_name='password_change.html',
            form_class=StyledPasswordChangeForm,
        ),
        name='password_change',
    ),
    path(
        'account/password/done/',
        auth_views.PasswordChangeDoneView.as_view(template_name='password_change_done.html'),
        name='password_change_done',
    ),
]
