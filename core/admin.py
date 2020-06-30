from django.contrib import admin

from core.models import ResourceMapping


class ResourceMappingAdmin(admin.ModelAdmin):
    list_display = ('uid', 'pid', 'category', 'last_update')
    list_filter = ('category',)
    search_fields = ('uid', 'pid', 'category', 'last_update')


admin.site.register(ResourceMapping, ResourceMappingAdmin)
