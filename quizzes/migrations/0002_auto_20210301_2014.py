# Generated by Django 3.1.5 on 2021-03-01 20:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'tags',
            },
        ),
        migrations.AddField(
            model_name='quiz',
            name='tags',
            field=models.ManyToManyField(related_name='quizzes', to='quizzes.Tag'),
        ),
    ]
