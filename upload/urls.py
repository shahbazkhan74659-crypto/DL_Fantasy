from django.urls import path

from . import views

urlpatterns = [
    path('', views.upload_hub, name='upload_hub'),
    path('godvalley/', views.upload_godvalley, name='upload_godvalley'),
    path('fiction/', views.upload_fiction, name='upload_fiction'),
    path('philosophy/', views.upload_philosophy, name='upload_philosophy'),
    path('mythology/', views.upload_mythology, name='upload_mythology'),
    path('edit/<int:pk>/', views.edit_content, name='edit_content'),
    path('delete/<int:pk>/', views.delete_content, name='delete_content'),
    path('delete-cover/<int:pk>/', views.delete_content_cover, name='delete_content_cover'),
    path('collections/', views.upload_collections, name='upload_collections'),
    path('collections/edit/<int:pk>/', views.edit_collection, name='edit_collection'),
    path('collections/delete/<int:pk>/', views.delete_collection, name='delete_collection'),
    path('collections/delete-cover/<int:pk>/', views.delete_collection_cover, name='delete_collection_cover'),
    path('collections/items/<int:pk>/move/', views.move_collection_item, name='move_collection_item'),
]
