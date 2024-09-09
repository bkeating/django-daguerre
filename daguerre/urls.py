from django.urls import re_path

from daguerre.views import (AdjustedImageRedirectView, AjaxAdjustmentInfoView,
                            AjaxUpdateAreaView)


urlpatterns = [
    re_path(r'^adjust/(?P<storage_path>.+)$',
        AdjustedImageRedirectView.as_view(),
        name="daguerre_adjusted_image_redirect"),
    re_path(r'^info/(?P<storage_path>.+)$',
        AjaxAdjustmentInfoView.as_view(),
        name="daguerre_ajax_adjustment_info"),
    re_path(r'^area/(?P<storage_path>.+?)(?:/(?P<pk>\d+))?$',
        AjaxUpdateAreaView.as_view(),
        name="daguerre_ajax_update_area"),
]
