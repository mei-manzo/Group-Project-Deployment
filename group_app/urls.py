from django.urls import path     
from . import views
# from django.conf import settings
# from django.conf.urls.static import static

urlpatterns = [
    path('', views.index),
    path('check_registration', views.check_registration),
    path('check_login', views.check_login),
    path('logout', views.logout),
    path('subscriptions/<str:order_by>/<int:page_num>', views.subscriptions),
    path('stats/<int:subscription_id>', views.stats),
    path('user_account', views.user_account),
    path('process_edit_user', views.process_edit_user),
    path('add_subscription', views.add_subscription),
    path('process_add_subscription', views.process_add_subscription),
    path('edit_subscription/<int:subscription_id>', views.edit_subscription),
    path('process_edit_subscription/<int:subscription_id>', views.process_edit_subscription),
    path('delete_subscription', views.delete_subscription),
    path('select_sub_to_view', views.select_sub_to_view),
]