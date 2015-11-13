Редактируемые в панеле управления шаблоны для sms/email
python 2.7/3.4+, django 1.7+

## Установка

```
pip install git+git://github.com/aderugin/django-notifier.git
```

```python
INSTALLED_APPS = (
    ...
    'django_notifier',
    ...
)
```

## Использование

### Создание email шаблона

```python
# settings.py
# В константе DJANGO_NOTIFIER_ACTIONS необходимо определить список событий уведомления
# Каждое событие определяет (<машинное имя>, <название>, [<список переменных>])
DJANGO_NOTIFIER_ACTIONS = (
    ('user_create_post', 'Создан пост', ['TITLE', 'TEXT']),
)


# models.py
from django.db import models
from django_notifier.models import EmailTemplate as BaseEmailTemplate, Template
from django_notifier.models import post_save_signal_notifier

class EmailTemplate(BaseEmailTemplate):
    """
    По умолчанию, письмо отправляется стандартными механизмами Django
    Чтобы это изменить, нужно переопределить метод "send_message"
    """
    pass

# Декорируем класс, теперь при создании поста
# будут отправлены уведомления по событию "user_create_post"
@post_save_signal_notifier('user_create_post')
class Post(models.Model):
    # ...

# Также можно определить свой сигнал на отправку уведомлений
# сделать это можно при помощи декоратора "custom_signal_notifier"
@custom_signal_notifier('user_create_post', custom_signal)
class Post(models.Model):
    # ...


# admin.py
from django_notifier.admin import BaseTemplateForm, BaseTemplateAdmin
from .models import EmailTemplate

class EmailTemplateForm(BaseTemplateForm):
    class Meta:
        model = EmailTemplate
        fields = '__all__'

class EmailTemplateAdmin(BaseTemplateAdmin):
    form = EmailTemplateForm

admin.site.register(EmailTemplate, EmailTemplateAdmin)
```
