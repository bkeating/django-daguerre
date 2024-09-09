from django.urls import path

from daguerre.views import (AdjustedImageRedirectView, AjaxAdjustmentInfoView,
                            AjaxUpdateAreaView)


urlpatterns = [
    path('adjust/<path:storage_path>',
         AdjustedImageRedirectView.as_view(),
         name="daguerre_adjusted_image_redirect"),
    path('info/<path:storage_path>',
         AjaxAdjustmentInfoView.as_view(),
         name="daguerre_ajax_adjustment_info"),
    path('area/<path:storage_path>/<int:pk>',
         AjaxUpdateAreaView.as_view(),
         name="daguerre_ajax_update_area"),
    path('area/<path:storage_path>',
         AjaxUpdateAreaView.as_view(),
         name="daguerre_ajax_update_area"),
]
