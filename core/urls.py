from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('writings/', views.writings, name='writings'),
    path('writings/<slug:category>/', views.writings_category_list, name='writings_category_list'),
    path('writings/<slug:category>/<slug:slug>/', views.writings_detail, name='writings_detail'),
    path('godvalley/', views.godvalley_list, name='godvalley_list'),
    path('godvalley/<slug:slug>/', views.godvalley_detail, name='godvalley_detail'),
    path('about/', views.about, name='about'),
]
