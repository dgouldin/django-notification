from django.conf.urls.defaults import *

from notification.views import notices, mark_all_seen, feed_for_user, single, delete, archive, mark_seen

urlpatterns = patterns('',
    url(r'^$', notices, name="notification_notices"),
    url(r'^(\d+)/$', single, name="notification_notice"),
    url(r'^delete/(?P<noticeid>\d+)/$', delete, name="notification_delete"),
    url(r'^archive/(?P<noticeid>\d+)/$', archive, name="notification_archive"),
    url(r'^mark_seen/(?P<noticeid>\d+)/$', mark_seen, name="notification_mark_seen"),
    url(r'^feed/$', feed_for_user, name="notification_feed_for_user"),
    url(r'^mark_all_seen/$', mark_all_seen, name="notification_mark_all_seen"),
)
