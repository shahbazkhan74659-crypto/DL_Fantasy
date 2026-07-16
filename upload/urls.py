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
]
