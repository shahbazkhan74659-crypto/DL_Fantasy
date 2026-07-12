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
    path('feed/', LatestContentFeed(), name='feed'),
    path('archive/', views.archive, name='archive'),
    path('concepts/', views.concepts, name='concepts'),
    path('collections/', views.collections, name='collections'),
    path('about/', views.about, name='about'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('account/', views.account, name='account'),
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
