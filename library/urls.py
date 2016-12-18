from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^$', views.main, name='main'),
    url(r'^signin', views.signin, name='signin'),
    url(r'^logout', views.logout, name='logout'),
    url(r'^signup', views.signup, name='signup'),
    url(r'^reg', views.reg, name='reg'),
    url(r'^check_user', views.check_user, name='check_user'),
    url(r'^admin', views.admin, name='admin'),
    url(r'^delete_book', views.delete_book, name='delete_book'),
    url(r'^add_book', views.add_book, name='add_book'),
    url(r'^edit_book', views.edit_book, name='edit_book'),
    url(r'^dump', views.dump, name='dump'),
    url(r'^restore', views.restore, name='restore'),
    url(r'^search', views.search, name='search'),
    url(r'^book', views.book, name='book'),
    url(r'^top100', views.top100, name='top100'),
    url(r'^statistics', views.statistics, name='statistics'),


]