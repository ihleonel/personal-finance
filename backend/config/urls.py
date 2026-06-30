"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('modules.auths.infrastructure.urls')),
    path('api/accounts/', include('modules.accounts.infrastructure.urls')),
    path('api/categories/', include('modules.categories.infrastructure.urls')),
    path('api/transactions/', include('modules.transactions.infrastructure.urls')),
]
