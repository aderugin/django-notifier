# -*- coding: utf-8 -*-
from django.contrib import admin
from django import forms
from django.shortcuts import redirect
from django.core.urlresolvers import reverse


class BaseTemplateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(BaseTemplateForm, self).__init__(*args, **kwargs)
        self.fields['action'].widget.attrs['class'] = 'js-variables-switcher'
        self.fields['to'].widget.attrs['class'] = 'js-recipient-switcher'


class BaseTemplateAdmin(admin.ModelAdmin):
    readonly_fields = 'variables_field',

    class Media:
        js = 'admin/notifier.min.js',


class SingleTemplateAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        if self.model.objects.count() > 0:
            return False
        else:
            return True

    def changelist_view(self, request, extra_context=None):
        info = '{0}_{1}'.format(self.model._meta.app_label, self.model._meta.model_name)
        try:
            instance = self.model.objects.get()
        except self.model.DoesNotExist:
            return redirect(reverse('admin:{0}_add'.format(info)))
        else:
            return redirect(reverse('admin:{0}_change'.format(info), args=[instance.pk]))

    def get_form(self, *args, **kwargs):
        form = super(SingleTemplateAdmin, self).get_form(*args, **kwargs)
        help_text = form.base_fields['item'].help_text
        form.base_fields['item'].help_text = help_text % self.model.get_item_variables()
        return form
