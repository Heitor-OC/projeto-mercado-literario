from django.shortcuts import render
from django.http import JsonResponse
from .models import Book, Category
import re
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from .templatetags.custom_tags import pretty_category
from django.core.paginator import Paginator
from django.template.loader import render_to_string
import pandas as pd
import plotly.express as px
import plotly.io as pio
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.cluster import KMeans
import io
import base64
import matplotlib
matplotlib.use('Agg')

def render_home(request):
    num_categories = Category.objects.count()
    num_books = Book.objects.count()
    
    context = {
        'num_categories': num_categories,
        'num_books': num_books,
    }
    
    return render(request, 'books/home.html', context)

def parse_price(price_str):
    cleaned_price = re.sub(r'[^\d,\.]', '', price_str)
    cleaned_price = cleaned_price.replace(',', '.')
    try:
        return float(cleaned_price)
    except ValueError:
        return None

def save_books_data(books_data):
    for book_data in books_data:
        try:
            book_id = book_data['id']
            category_name = book_data['body']['category']
            title = book_data['body']['title']
            old_price_str = book_data['body']['price'].get('price_old', None)
            new_price_str = book_data['body']['price']['price_new']
            image_url = book_data['body'].get('image_url', None)

            old_price = parse_price(old_price_str) if old_price_str else None
            new_price = parse_price(new_price_str)

            if new_price is None:
                continue 

            category, created = Category.objects.get_or_create(name=category_name)

            book, created = Book.objects.get_or_create(
                id=book_id,
                defaults={
                    'category': category,
                    'title': title,
                    'old_price': old_price,
                    'new_price': new_price,
                    'image_url': image_url,
                }
            )
            if not created:
                book.category = category
                book.title = title
                book.old_price = old_price
                book.new_price = new_price
                book.image_url = image_url
                book.save()
        except Exception:
            continue 

    return JsonResponse({'status': 'success'}, status=201)

def group_books_by_category(books):
    grouped_books = defaultdict(list)
    for book in books:
        grouped_books[book.category.name].append(book)
    return grouped_books

def scrape_form(request):
    return render(request, 'books/scrape_form.html')

def fix_category(category):
    category = category.strip().lower()
    category = category.replace(' & ', '-e-')
    category = category.replace('á', 'a')
    category = category.replace('ã', 'a')
    category = category.replace('õ', 'o')
    category = category.replace('â', 'a')
    category = category.replace('ó', 'o')
    category = category.replace('é', 'e')
    category = category.replace('í', 'i')
    category = category.replace('ú', 'u')
    category = category.replace('ê', 'e')
    category = category.replace('ç', 'c')
    category = category.replace(',', '')
    category = category.replace(' ', '-')
    return category

def fetch_categories():
    try:
        url = 'https://leitura.com.br/livros/ciencia?page=1'
        res = requests.get(url)
        html = res.text
        soup = BeautifulSoup(html, 'html.parser')

        categories = soup.find_all('div', class_='dropdown-inner')[0].find_all('li')

        list_categories = []
        for cat in categories:
            try:
                category = cat.find('a').text
                fixed_category = fix_category(category)
                list_categories.append(fixed_category)

                Category.objects.get_or_create(name=fixed_category)
            except Exception:
                continue
        
        return list_categories
    except Exception:
        return []

def fetch_data(category, page):
    try:
        url = f'https://leitura.com.br/livros/{category}?page={page}'
        res = requests.get(url)
        html = res.text
        soup = BeautifulSoup(html, 'html.parser')
        
        divs_books = soup.find_all('div', class_='product-layout')
        
        books = []
        
        for item in divs_books:
            try:
                title = item.find('h4').text
                price_tag = item.find('p', class_='price')
                image_url = item.find('img', class_='img-responsive')['src']
                
                if price_tag.find('span'):
                    old_price = price_tag.find('span', class_='price-old').text.strip()
                    new_price = price_tag.find('span', class_='price-new').text.strip()
                    price = {'price_old': old_price, 'price_new': new_price}
                else:
                    price = {'price_old': None, 'price_new': price_tag.text.strip()}
                
                book_info = {
                    'title': title,
                    'image_url': image_url,
                    'price': price
                }
                books.append(book_info)
            except Exception:
                continue
                
        return books
    except Exception:
        return []

def scrape_books(request):
    if request.method == 'POST':
        num_pages = int(request.POST.get('pages', 1))
        categories = fetch_categories()
        all_books = []
        id_counter = 1

        for category in categories:
            for page in range(1, num_pages + 1):
                books = fetch_data(category, page)
                for book in books:
                    book_data = {
                        'id': id_counter,
                        'body': {
                            'category': category,
                            'title': book['title'],
                            'price': book['price'],
                            'image_url': book['image_url']
                        }
                    }
                    all_books.append(book_data)
                    id_counter += 1

        return save_books_data(all_books)
    else:
        return JsonResponse({'status': 'fail', 'message': 'Only POST method is allowed'}, status=405)


def category_list(request):
    categories = Category.objects.all()
    return render(request, 'books/category_list.html', {'categories': categories})


def display_books(request):
    category_name = request.GET.get('category')
    if category_name:
        books = Book.objects.filter(category__name=category_name)
    else:
        books = Book.objects.all()

    grouped_books = defaultdict(list)
    for book in books:
        grouped_books[book.category.name].append(book)

    paginated_books = {}
    for category, books in grouped_books.items():
        paginator = Paginator(books, 8)  
        page_number = request.GET.get(f'page_{category}', 1)
        paginated_books[category] = paginator.get_page(page_number)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        category = request.GET.get('category')
        page_obj = paginated_books[category]
        books_html = render_to_string('books/book_list.html', {'page_obj': page_obj})
        pagination_html = render_to_string('books/pagination.html', {'page_obj': page_obj, 'category': category})
        return JsonResponse({'books_html': books_html, 'pagination_html': pagination_html})

    return render(request, 'books/books.html', {
        'grouped_books': paginated_books,
        'selected_category': category_name,
    })
    

def get_graph():
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    graph = base64.b64encode(image_png).decode('utf-8')
    plt.close() 
    return graph


def market_analysis(request):
    books = Book.objects.all()
    df = pd.DataFrame(list(books.values('category__name', 'title', 'new_price')))
   
    df['category__name'] = df['category__name'].apply(pretty_category)
    
    mean_price_per_category = df.groupby('category__name')['new_price'].mean().reset_index()
    mean_price_per_category.columns = ['category', 'mean_price']
    
    # Gráfico de barras: Média de Preços por Categoria
    bar_fig = px.bar(
        mean_price_per_category,
        x='category',
        y='mean_price',
        title='Média de Preços por Categoria',
        labels={'category': 'Categoria', 'mean_price': 'Preço Médio'},
        color='category',
        hover_data=['category', 'mean_price']
    )
    bar_fig.update_traces(marker=dict(line=dict(width=0)))  
    bar_fig.update_layout(
        bargap=0.0,  
        bargroupgap=0.0,  
    )

    bar_graph = pio.to_html(bar_fig, full_html=False)

    # Gráfico de pizza: Quantidade de livros por categoria
    category_counts = df['category__name'].value_counts().reset_index()
    category_counts.columns = ['category', 'count']
    pie_fig = px.pie(
        category_counts,
        names='category',
        values='count',
        title='Quantidade de Livros por Categoria',
        color_discrete_sequence=px.colors.qualitative.Set3,
        hover_data=['category', 'count']
    )
    
    pie_fig.update_layout(
        xaxis=dict(showticklabels=False),
        width=800,
        height=600
    )
    pie_chart = pio.to_html(pie_fig, full_html=False)

   # Scatterplot: Preços de cada livro com hue por categoria
    scatter_fig = px.scatter(
        df,
        x='title',
        y='new_price',
        color='category__name',
        title='Preços de Cada Livro',
        labels={'title': 'Título', 'new_price': 'Preço', 'category__name': 'Categoria'},
        hover_data={'title': True, 'new_price': True, 'category__name': True},
        template='plotly_white'
    )
    scatter_fig.update_layout(
        xaxis=dict(showticklabels=False),
        width=1750,
        height=600
    )
    scatter_plot = pio.to_html(scatter_fig, full_html=False)


    # Gráfico de dispersão interativo para clustering
    df_encoded = pd.get_dummies(df['category__name'])
    df_encoded['new_price'] = df['new_price']
    kmeans = KMeans(n_clusters=5)
    df['cluster'] = kmeans.fit_predict(df_encoded)
    cluster_fig = px.scatter(
        df,
        x='title',
        y='new_price',
        color='cluster',
        title='Clusters de Preços de Livros',
        labels={'title': 'Título', 'new_price': 'Preço', 'cluster': 'Cluster'},
        hover_data=['title', 'new_price', 'cluster'],
        template='plotly_white'
    )
    cluster_fig.update_layout(
        xaxis=dict(showticklabels=False),
        width=1750,
        height=600
    )
    scatter_cluster = pio.to_html(cluster_fig, full_html=False)

    # Regressão linear
    X_train, X_test, y_train, y_test = train_test_split(df_encoded.drop(columns=['new_price']), df_encoded['new_price'], test_size=0.2, random_state=42)
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    regression_fig, ax = plt.subplots(figsize=(10, 6))
    sns.regplot(x=y_test, y=y_pred, ax=ax)
    ax.set_xlabel('Preços Reais')
    ax.set_ylabel('Preços Preditos')
    ax.set_title('Regressão Linear: Preço Real vs Predito')
    graph = get_graph()

    # Gráfico de linha: Quantidade de livros por categoria
    line_fig = px.line(
        category_counts,
        x='category',
        y='count',
        title='Quantidade de Livros por Categoria',
        labels={'category': 'Categoria', 'count': 'Quantidade'},
        markers=True
    )
    line_chart = pio.to_html(line_fig, full_html=False)
    
    context = {
        'bar_graph': bar_graph,
        'pie_chart': pie_chart,
        'scatter_plot': scatter_plot,
        'scatter_cluster': scatter_cluster,
        'regression_plot': graph,
        'r2_score': r2,
        'mse': mse,
        'line_chart': line_chart,  
    }

    return render(request, 'books/market_analysis.html', context)

