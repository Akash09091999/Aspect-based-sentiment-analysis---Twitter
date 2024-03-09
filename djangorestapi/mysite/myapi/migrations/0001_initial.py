# Generated by Django 2.2.9 on 2020-03-31 10:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AspectMeta',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('aspect', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='TweetMeta',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('twitter_id', models.BigIntegerField(default=0)),
                ('tweet_timestamp', models.DateTimeField(null=True)),
                ('tweet_hashtag', models.CharField(max_length=100)),
                ('crawler_lastexecutiontime', models.DateTimeField(null=True)),
                ('is_deleted', models.IntegerField(default=0)),
                ('if_first', models.IntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='DateWiseSentimentForAspect',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('sentiment_value', models.FloatField()),
                ('aspect', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapi.AspectMeta')),
            ],
        ),
        migrations.CreateModel(
            name='DateWiseSentiment',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('date', models.DateField()),
                ('sentiment_average', models.FloatField()),
                ('local_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapi.TweetMeta')),
            ],
        ),
        migrations.AddField(
            model_name='aspectmeta',
            name='hashtag',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myapi.TweetMeta'),
        ),
    ]