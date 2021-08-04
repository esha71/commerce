from django.contrib import admin

# Register your models here.
from auctions.models import Category


class BaseAdmin(admin.ModelAdmin):
    exclude = ('created_on', 'created_by', 'modified_by')


    def save_model(self, request, obj, form, change):
        if form.changed_data:
            obj.modified_by = request.user
            super(BaseAdmin, self).save_model(request, obj, form, change)

    def get_exclude(self, request, obj=None):
        return self.exclude


@admin.register(Category)
class ActivityAdmin(BaseAdmin):
    pass