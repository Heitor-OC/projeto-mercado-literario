function loadPage(category, page) {
    var url = $('#books-container-' + category).data('url');
    var data = {
        'category': category
    };
    data['page_' + category] = page;

    $.ajax({
        url: url,
        data: data,
        success: function(data) {
            $('#books-container-' + category).html(data.books_html);
            $('#pagination-container-' + category).html(data.pagination_html);
        },
        error: function(xhr, status, error) {
            console.log(xhr.responseText);
        }
    });
}
