from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('',views.home,name="home"),
    path('tweetAnalysis/', views.tweetAnalysis,name="tweetAnalysis"),
    path('downloadFile/', views.downloadFile,name="downloadFile"),
    path('interestAnalysis/',views.interestAnalysis,name="viewsAnalysis"),
    path('targetedAds/' , views.targetedAds, name="targetedAds")
]
