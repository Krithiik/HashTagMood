from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('',views.home,name="home"),
    path('tweetCount/',views.tweetCount,name="tweetCount"),
    path('targetedAds/',views.targetedAds,name="targetedAds"),
    path('sentimentAnalysis/',views.sentimentAnalysis,name="sentimentAnalysis"),
    path('hashtagAnalysis/',views.hashtagAnalysis,name="hashtagAnalysis"),
    path('hashtagForm/', views.hashtagForm, name="hashtagForm"),
    path('downloadFile/', views.downloadFile,name="downloadFile"),
    path('interestAnalysis/',views.interestAnalysis,name="viewsAnalysis"),
]
