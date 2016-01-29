from django.contrib import admin
from .models import WXUser, Leave
# Register your models here.


@admin.register(WXUser)
class WXUserAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'work_num', 'sex', 'email', 'direct_director', 'dept_leader',
                    'working_years', 'company_working_years', 'legal_vacation_days', 'company_vacation_days',
                    'is_leader')
    search_fields = ('name', 'department')
    readonly_fields = ('wx_openid', 'wx_nickname')
    list_filter = (
        ('department', admin.AllValuesFieldListFilter),
    )



@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    search_fields = ('applicant_name', 'group')
    readonly_fields = ('applicant_name', 'group', 'type', 'create_time', 'leave_start_datetime', 'leave_end_datetime',
                       'leave_days', 'status', 'leave_reason', 'remark', 'next_dealer', 'deal_end_time',
                       'refuse_reason', 'show_attach_photo_for_admin')
    list_display = ('applicant_name', 'group', 'type', 'create_time', 'leave_start_datetime', 'leave_end_datetime',
                    'leave_days', 'status')
    exclude = ('applicant_openid', 'attach_photo')
    list_filter = (
        ('group', admin.ChoicesFieldListFilter),
        ('type', admin.ChoicesFieldListFilter),
    )

    def get_actions(self, request):
        """
        remove delete_selected function in model list in admin
        :param request:
        :return:
        """
        actions = super(LeaveAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        """
        remove delete btn in admin
        :param request:
        :param obj:
        :return:
        """
        return False

    def has_add_permission(self, request, obj=None):
        return False

    class Media:
        from django.conf import settings
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        # edit this path to wherever
        css = {'all': (media_url+'css/no-addanother-button.css',)}


    # def change_view(self, request, object_id, form_url='', extra_context=None):
    #     extra_context = extra_context or {}
    #     extra_context['show_save_and_add_another'] = False
    #     # or
    #     extra_context['really_hide_save_and_add_another_damnit'] = True
    #     return super(LeaveAdmin, self).change_view(request, object_id,
    #         form_url, extra_context=extra_context)



    # def has_module_permission((self, request, obj=None):
    #     return False