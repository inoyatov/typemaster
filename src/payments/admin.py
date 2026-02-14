from django.contrib import admin

from payments.models import Subscription, SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "duration_days", "price", "is_active")
    list_filter = ("is_active",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "starts_at", "expires_at")
    list_filter = ("plan",)
    search_fields = ("user__email",)
    raw_id_fields = ("user",)
