from django.contrib import admin
from django.contrib.auth.models import Group# admin.py
from .models import Spot, Node, User, AddedTag, Mapdata, Tag


class UserAdmin(admin.ModelAdmin):
    list_display = ("name", "is_superuser")
    readonly_fields = ('created_at', 'updated_at')
    ordering = ("-updated_at",)
    exclude = ("username", )

    fieldsets = (
        (None, {"fields": ("name",
                           "is_active", "created_at", "updated_at"
                           )}),
        ("Permissions", {
         "fields": ("is_superuser", "is_staff", "user_permissions")
         }),
    )


admin.site.register(User, UserAdmin)
admin.site.unregister(Group)

@admin.register(Spot)
class SpotAdmin(admin.ModelAdmin):
    list_display = ('idx', 'name', 'latitude', 'longitude', 'hp', 'tags')  # 存在するフィールドを指定
    
@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('idx', 'node', 'name', 'latitude', 'longitude', 'tags')  # 存在するフィールドを指定

@admin.register(AddedTag)
class AddedTagAdmin(admin.ModelAdmin):
    list_display = ('user', 'tag', 'spot', 'added_at')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('user', 'tag')
    

@admin.register(Mapdata)
class MapdataAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'distance', 'time', 'start_spot', 'goal_spot',
                    'aim_tags', 'html')
