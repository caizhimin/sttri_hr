from django.contrib import admin
from .models import WXUser, Leave
# Register your models here.


class WXUserAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'work_num', 'sex', 'email', 'direct_director', 'dept_leader',
                    'working_years', 'company_working_years', 'legal_vacation_days', 'company_vacation_days',
                    'is_leader')


class LeaveAdmin(admin.ModelAdmin):
    pass

admin.site.register(WXUser, WXUserAdmin)
admin.site.register(Leave, LeaveAdmin)