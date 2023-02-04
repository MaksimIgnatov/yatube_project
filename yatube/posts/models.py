from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

from core.models import CreatedModel

User = get_user_model()


class Post(CreatedModel):
    text = models.TextField(verbose_name='Текст поста',
                            help_text='Текст нового поста')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='posts', verbose_name='Автор',
                               help_text=('Группа, к которой будет '
                                          'относиться пост'))
    group = models.ForeignKey('Group', related_name='posts', blank=True,
                              null=True, on_delete=models.SET_NULL,
                              verbose_name='Группа',
                              help_text=('Группа, к которой будет '
                                         'относиться пост'))
    image = models.ImageField('Картинка',
                              upload_to='posts/',
                              blank=True)

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:settings.COUNT_SIGN_NAME_POST]


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(unique=True, verbose_name='URL')
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self) -> str:
        return self.title


class Comment(CreatedModel):
    post = models.ForeignKey('Post', related_name='comments',
                             on_delete=models.CASCADE,
                             verbose_name='Пост',
                             help_text=('Пост к которому '
                                        'относиться комментарий'))
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments', verbose_name='Автор')
    text = models.TextField(verbose_name='Текст')


class Follow(models.Model):
    user = models.ForeignKey(User, related_name='follower',
                             on_delete=models.CASCADE,
                             verbose_name='Пользователь')
    author = models.ForeignKey(User, related_name='following',
                               on_delete=models.CASCADE,
                               verbose_name='Автор')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_follow')
        ]
