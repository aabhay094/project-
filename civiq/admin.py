from django.contrib import admin

from .models import (
    CitizenFeedback,
    Complaint,
    ComplaintResolution,
    ComplaintTimelineEvent,
    Department,
    OfficerProfile,
    Sector,
    StaticPage,
    TeamMember,
)


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "head_name", "helpline_number", "emergency_number", "sla_hours")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("sectors",)
    search_fields = ("name", "head_name")


@admin.register(OfficerProfile)
class OfficerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "department", "designation", "is_active_officer")
    list_filter = ("department", "is_active_officer")
    search_fields = ("user__username", "user__first_name", "user__last_name")


class ComplaintTimelineInline(admin.TabularInline):
    model = ComplaintTimelineEvent
    extra = 0
    readonly_fields = ("created_at",)


class ComplaintResolutionInline(admin.StackedInline):
    model = ComplaintResolution
    extra = 0


class CitizenFeedbackInline(admin.StackedInline):
    model = CitizenFeedback
    extra = 0


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = (
        "tracking_id",
        "citizen_name",
        "sector",
        "department",
        "priority",
        "status",
        "assigned_officer",
        "created_at",
    )
    list_filter = ("status", "priority", "sector", "department")
    search_fields = ("tracking_id", "citizen_name", "citizen_phone", "nlp_tags")
    readonly_fields = ("tracking_id", "created_at", "updated_at")
    inlines = [ComplaintTimelineInline, ComplaintResolutionInline, CitizenFeedbackInline]


@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "show_in_footer", "updated_at")
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ("is_published", "show_in_footer")


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "department", "display_order", "is_ribhay_credit")
    list_editable = ("display_order",)
    list_filter = ("department", "is_ribhay_credit")
