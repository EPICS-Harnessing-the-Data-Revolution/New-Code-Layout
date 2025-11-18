"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.urls import path
from services.views import interactiveMap, customnoaagraph, customshadehillgraph, customgauge, customcocograph, customgaugegraph, customdam, customdamgraph, test, custommesonet, custommesonetgraph, tabs, tabstest, maptabs, homepage, forecast, about, register, signup, signin, signout
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from services.views import favorites, login, contactus
urlpatterns = [
    path('admin/', admin.site.urls),
    path('customgaugegraph/', customgaugegraph),
    path('customdamgraph/', customdamgraph),
    path('customcocograph/', customcocograph),
#    path('customgauge/', customgauge),
    path('customdam/', customdam),
    path('customnoaagraph/', customnoaagraph),
#    path('custommesonet/', custommesonet),
    path('custommesonetgraph/', custommesonetgraph),
    path('customshadehillgraph/', customshadehillgraph),
    path('map/', interactiveMap),
    path('homep/', test),
    path('home/', homepage),
#    path('tabs/', tabs),
#    path('tabstest/', tabstest),
    path('maptabs/', maptabs),
    path('', homepage),
    path('forecast/', forecast),
    path('about/', about),
    path('register/', register),
    path('signup', signup, name='signup'),
    path('signin', signin, name='signin'),
    path('signout', signout, name='signout'),
    path('favorites/', favorites, name='favorites'),
    path('login/', login, name='login'),
    path('contactus/', contactus, name='contactus'),
    path("accounts/", include("django.contrib.auth.urls"))
]

urlpatterns += staticfiles_urlpatterns()
