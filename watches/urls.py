from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('watches/', views.PriceWatchListView.as_view(), name='watch_list'),
    path('watches/create/', views.PriceWatchCreateView.as_view(), name='watch_create'),
    path('watches/<int:pk>/', views.PriceWatchDetailView.as_view(), name='watch_detail'),
    path('watches/<int:pk>/edit/', views.PriceWatchUpdateView.as_view(), name='watch_edit'),
    path('watches/<int:pk>/delete/', views.PriceWatchDeleteView.as_view(), name='watch_delete'),
    path('watches/<int:pk>/test/', views.test_watch_api, name='watch_test'),
    path('watches/<int:pk>/index-all/', views.index_all_watch_items, name='watch_index_all'),
    path('watches/<int:pk>/clear-reindex/', views.clear_and_reindex_watch_items, name='watch_clear_reindex'),
    path('watches/<int:pk>/clear-alerts/', views.clear_alerts, name='clear_alerts'),
    path('watches/<int:pk>/load-more/', views.load_more_underpriced, name='load_more_underpriced'),
    path('watches/<int:watch_id>/hide-item/<int:item_id>/', views.hide_underpriced_item, name='hide_underpriced_item'),
    path('api/parse-url/', views.parse_vinted_url, name='parse_vinted_url'),
]