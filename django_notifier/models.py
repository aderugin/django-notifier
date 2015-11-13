# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _
from django.utils.encoding import python_2_unicode_compatible
from django.contrib.auth import get_user_model
from django.utils import six
from django.db import models
from django.db.models.signals import post_save
from django.db.models.base import ModelBase
from django.conf import settings


def replace_text(text, variables):
    """
    Replace some special words in text to variable from dictionary
    @param text: raw text
    @param variables: dictionary of variables for replace
    """
    for name, value in variables.items():
        text = text.replace('#%s#' % name, str(value))
    return text


template_class_registry = []


def send_notifications(action, instance):
    """
    Sending all messages from all registred Template classes
    @param instance: instance of model that init action
    @param action: name of notification action
        get_notification_data is the method of model that returns
        dictionary of variables to replace it in template

        for example:
            def get_notification_data(self):
                return {
                    'ORDER_ID': self.id,
                    'ITEM_TITLE': self.product.name,
                    'ITEM_PRICE': self.product.price,
                    'USER_NAME': self.person,
                    'USER_PHONE': self.phone
                }
    """
    for template_class in template_class_registry:
        template_class.send_messages(action, instance.get_notification_data())


class TemplateMetaclass(ModelBase):
    def __new__(cls, name, bases, attrs):
        new_class = ModelBase.__new__(cls, name, bases, attrs)
        if not new_class._meta.abstract:
            template_class_registry.append(new_class)
        return new_class


ACTIONS = settings.DJANGO_NOTIFIER_ACTIONS
"""
For example:
    ACTIONS = (
        (<action machine name>, <action title>, <list of variables>),
        ('order_create', _('Order created'), ['ORDER_ID'])
    )
"""


@python_2_unicode_compatible
class Template(six.with_metaclass(TemplateMetaclass, models.Model)):
    """
    Abstarct class for notifications templates
        list_data_fields - additional fields that will include message
        recipient_exclude - exclude recipient by specified actions
            Example:
                recipient_exclude = {'order_create': 'USER'}
                It will exclude opportunity to choose 'USER' as recipient
                for action 'order_create'
    """
    DEFAULT_VARIABLES = ['DEFAULT_FROM']
    TO_CHOICES = [
        ('#ADMIN#', _('Administrator')),
        ('#USER#', _('User who made action'))
    ]

    _list_data_fields = ('sender', 'to', 'message')
    list_data_fields = ()
    recipient_exclude = dict()

    active = models.BooleanField(default=True, verbose_name=_('Activated'))
    action = models.CharField(verbose_name=_('Action'), max_length=255,
                              choices=[(action[0], action[1]) for action in ACTIONS])

    sender = models.CharField(verbose_name=_('Sender'), max_length=100, default='#DEFAULT_FROM#')
    to = models.CharField(verbose_name=_('Recipient'), choices=TO_CHOICES, max_length=10)
    message = models.TextField(verbose_name=_('Message'))

    class Meta:
        abstract = True

    def __str__(self):
        return u'%s — %s' % (self.get_action_display(), self.get_to_display())

    def variables_field(self):
        """
        Field what return list of variables by actions
        """
        html = ''

        for action, variables in self._get_actions_variables().items():
            html += '<div style="%s" class="js-variables-item" id="%s" '\
                'data-excluded-recipient="%s">%s</div>' % (
                    'display:none' if self.action != action else '',
                    action, self.recipient_exclude.get(action, ''),
                    ', '.join(['#%s#' % v for v in variables])
                )

        return '<div class="js-variables">%s</div>' % html

    variables_field.allow_tags = True
    variables_field.short_description = _('Available variables')

    @classmethod
    def send_messages(cls, action, variables=None):
        """
        Sending messages
        """
        variables = variables or {}
        for template in cls.objects.filter(action=action, active=True):
            template.send_message(template._get_prepared_data(variables))
        return True

    def get_data(self):
        """
        Return dict of fields what included in message body
        """
        return {field: getattr(self, field) for field in
                self._list_data_fields + self.list_data_fields}

    def update_variables(self, variables):
        """
        Updating variables dict
        """
        return variables

    def send_message(self, data):
        """
        Definition of sending process
        """
        raise NotImplementedError

    def _get_actions_variables(self):
        return {action[0]: self.DEFAULT_VARIABLES + action[2] for action in ACTIONS}

    def _get_prepared_data(self, variables):
        variables = self.update_variables(variables)
        return dict((key, replace_text(value, variables)) for key, value in self.get_data().items())


@python_2_unicode_compatible
class ItemListTemplate(models.Model):
    """
    Abstract class for templating of every item in list of items
    """
    ITEM_VARIABLES = []

    item_list = models.TextField(verbose_name=_('Template for list of items'),
                                 default='#ITEM_LIST#', help_text=_('Available variables: %s') % '#ITEM_LIST#')
    item = models.TextField(verbose_name=_('Template for single items'),
                            help_text=_('Available variables: %s'))

    class Meta:
        abstract = True

    @classmethod
    def get_prepared_text(cls, items):
        template = cls.objects.first()
        if template:
            text = ''
            for item in items:
                text += replace_text(template.item, item.get_notification_data())
            return replace_text(template.item_list, {'ITEM_LIST': text})
        return ''

    @classmethod
    def get_item_variables(cls):
        return ', '.join(['#%s#' % v for v in cls.ITEM_VARIABLES])


@python_2_unicode_compatible
class EmailTemplate(Template):
    """
    Email message
    """
    list_data_fields = 'subject',

    subject = models.CharField(max_length=200, verbose_name=_('Subject'))

    class Meta:
        abstract = True
        verbose_name = _('Email template')
        verbose_name_plural = _('Email templates')

    def get_data(self):
        data = super(EmailTemplate, self).get_data()
        data['subject'] = self.subject
        return data

    def update_variables(self, variables):
        variables = super(EmailTemplate, self).update_variables(variables)
        variables.update({
            'DEFAULT_FROM': settings.DEFAULT_FROM_EMAIL,
            'USER': variables.get('USER_EMAIL', ''),
            'ADMIN': ','.join([user.email for user in get_user_model().objects.all()]),
        })
        return variables

    def send_message(self, data):
        from django.core.mail import EmailMessage
        try:
            email = EmailMessage(data['subject'], data['message'], data['sender'], data['to'].split(','))
            email.content_subtype = 'html'
            email.send()
        except Exception:
            pass


def post_save_signal_notifier(action):
    """
    Decorator for model class that send notifications by post_save signal
    """
    def decorator(cls):
        if not hasattr(cls, 'get_notification_data'):
            raise AttributeError("You must to define 'get_notification_data'"
                                 "method for %s" % cls.__name__)

        def send_notifications_handler(sender, instance, created, **kwargs):
            if created:
                send_notifications(action, instance)
        post_save.connect(send_notifications_handler, sender=cls, weak=False)
        return cls
    return decorator


def custom_signal_notifier(action, signal):
    """
    Decorator for model class that send notifications by custom signal
    """
    def decorator(cls):
        if not hasattr(cls, 'get_notification_data'):
            raise AttributeError("You must to define 'get_notification_data'"
                                 "method for %s" % cls.__name__)

        def send_notifications_handler(sender, instance, **kwargs):
            send_notifications(action, instance)
        signal.connect(send_notifications_handler, sender=cls, weak=False)
        return cls
    return decorator
