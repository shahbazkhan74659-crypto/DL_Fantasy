from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('writings/', views.writings, name='writings'),
    path('writings/<slug:category>/', views.writings_category_list, name='writings_category_list'),
    path('writings/<slug:category>/<slug:slug>/', views.writings_detail, name='writings_detail'),
    path('godvalley/', views.godvalley_list, name='godvalley_list'),
    path('godvalley/chapters/', views.godvalley_chapters, name='godvalley_chapters'),
    path('godvalley/<slug:slug>/', views.godvalley_detail, name='godvalley_detail'),
    path('archive/', views.archive, name='archive'),
    path('concepts/', views.concepts, name='concepts'),
    path('collections/', views.collections, name='collections'),
    path('about/', views.about, name='about'),
]
