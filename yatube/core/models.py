from django.db import models


class CreatedModel(models.Model):
    text = models.TextField(
        verbose_name='Текст'
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='date'
    )

    class Meta:
        abstract = True
        ordering = ['-created']
