from django.contrib import admin

# Register your models here.
from auctions.models import Category, Bids, Listing, Watchlist, User, Comments


class BaseAdmin(admin.ModelAdmin):
    exclude = ('created_on', 'modified_on', 'modified_by')


    def save_model(self, request, obj, form, change):
        if form.changed_data:
            obj.modified_by = request.user
            super(BaseAdmin, self).save_model(request, obj, form, change)

    def get_exclude(self, request, obj=None):
        return self.exclude



#admin.site.register(User)
admin.site.register(Category, BaseAdmin)
admin.site.register(Bids, BaseAdmin)
admin.site.register(Listing, BaseAdmin)
#admin.site.register(Watchlist)
admin.site.register(Comments, BaseAdmin)
