from djongo import models

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Book(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    old_price = models.FloatField(null=True, blank=True)
    new_price = models.FloatField()
    image_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.title
