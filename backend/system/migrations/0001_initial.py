# Generated by Django 2.1.5 on 2019-02-05 12:30

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('text', models.TextField(help_text='正文', verbose_name='正文')),
            ],
            options={
                'verbose_name': '新闻',
                'verbose_name_plural': '新闻',
            },
        ),
        migrations.CreateModel(
            name='Setting',
            fields=[
                ('key', models.SlugField(primary_key=True, serialize=False, verbose_name='键')),
                ('value', models.CharField(max_length=200, verbose_name='值')),
            ],
            options={
                'verbose_name': '全局设置',
                'verbose_name_plural': '全局设置',
            },
        ),
        migrations.CreateModel(
            name='Version',
            fields=[
                ('id', models.SlugField(help_text='版本', max_length=20, primary_key=True, serialize=False, verbose_name='版本')),
                ('url', models.FileField(help_text='更新文件', upload_to='', verbose_name='更新文件')),
                ('testing', models.BooleanField(default=False, help_text='显示测试服入口', verbose_name='显示测试服入口')),
            ],
            options={
                'verbose_name': '游戏版本',
                'verbose_name_plural': '游戏版本',
            },
        ),
    ]
