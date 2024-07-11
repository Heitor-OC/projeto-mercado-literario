# Generated by Django 5.0.6 on 2024-06-26 20:24

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('category', models.CharField(max_length=200)),
                ('title', models.CharField(max_length=200)),
                ('old_price', models.FloatField(null=True)),
                ('new_price', models.FloatField()),
            ],
        ),
    ]
