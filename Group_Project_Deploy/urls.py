"""Group_Project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.urls import path, include  

# to use admin dashboard
from django.contrib import admin
from group_app.models import User, Subscription, Company, DataPoint
class UserAdmin(admin.ModelAdmin):
    pass
admin.site.register(User, UserAdmin)
class SubscriptionAdmin(admin.ModelAdmin):
    pass
admin.site.register(Subscription, SubscriptionAdmin)
class CompanyAdmin(admin.ModelAdmin):
    pass
admin.site.register(Company, CompanyAdmin)
class DataPointAdmin(admin.ModelAdmin):
    pass
admin.site.register(DataPoint, DataPointAdmin)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('group_app.urls')),
]
