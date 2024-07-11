from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.render_home, name='home'),
    path('save_books/', views.save_books_data, name='save_books'),
    path('books/', views.display_books, name='display_books'),
    path('scrape_form/', views.scrape_form, name='scrape_form'),
    path('scrape_books/', views.scrape_books, name='scrape_books'),
    path('market-analysis/', views.market_analysis, name='market_analysis'),
    path('categorias/', views.category_list, name='category_list'),
]
