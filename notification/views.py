from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.template import RequestContext
from django.utils import simplejson
from django.contrib.auth.decorators import login_required
from django.contrib.syndication.views import feed

from notification.models import *
from notification.decorators import basic_auth_required, simple_basic_auth_callback
from notification.feeds import NoticeUserFeed

# Pulled from django-voting
def json_error_response(error_message):
    return HttpResponse(simplejson.dumps(dict(success=False,
                                              error_message=error_message)))

@basic_auth_required(realm='Notices Feed', callback_func=simple_basic_auth_callback)
def feed_for_user(request):
    url = "feed/%s" % request.user.username
    return feed(request, url, {
        "feed": NoticeUserFeed,
    })

@login_required
def notices(request):
    notice_types = NoticeType.objects.all()
    notices = Notice.objects.notices_for(request.user, on_site=True)
    settings_table = []
    for notice_type in NoticeType.objects.all():
        settings_row = []
        for medium_id, medium_display in NOTICE_MEDIA:
            form_label = "%s_%s" % (notice_type.label, medium_id)
            setting = get_notification_setting(request.user, notice_type, medium_id)
            if request.method == "POST":
                if request.POST.get(form_label) == "on":
                    setting.send = True
                else:
                    setting.send = False
                setting.save()
            settings_row.append((form_label, setting.send))
        settings_table.append({"notice_type": notice_type, "cells": settings_row})
    
    notice_settings = {
        "column_headers": [medium_display for medium_id, medium_display in NOTICE_MEDIA],
        "rows": settings_table,
    }
    
    return render_to_response("notification/notices.html", {
        "notices": notices,
        "notice_types": notice_types,
        "notice_settings": notice_settings,
    }, context_instance=RequestContext(request))

@login_required
def single(request, id):
    notice = get_object_or_404(Notice, id=id)
    if request.user == notice.user:
        return render_to_response("notification/single.html", {
            "notice": notice,
        }, context_instance=RequestContext(request))
    raise Http404

def _action(request, noticeid=None, next_page=None, action=None):
    if not callable(action):
        raise ValueError("action must be a callable")
        
    next_page = next_page or request.REQUEST.get('next') or request.META.get('HTTP_REFERER')
    if request.method != 'POST':
        if request.is_ajax():
            return json_error_response('Please use POST for an action call.')
        else:
            return HttpResponseRedirect(next_page)

    if noticeid:
        try:
            notice = Notice.objects.get(id=noticeid)
            error_message = action(notice)
            if error_message:
                if request.is_ajax():
                    return json_error_response('You do not have permission to archive this notice.')
                else:
                    return HttpResponseRedirect(next_page)
        except Notice.DoesNotExist:
            if request.is_ajax():
                return json_error_response('Notice does not exist.')
            else:
                return HttpResponseRedirect(next_page)
    if request.is_ajax():
        status = simplejson.dumps({'status': "success"})
        return HttpResponse(status, mimetype="application/json")
    else:
        return HttpResponseRedirect(next_page)

@login_required
def archive(request, noticeid=None, next_page=None):
    def _archive(notice):
        if request.user == notice.user or request.user.is_superuser:
            notice.archive()
        else:   # you can archive other users' notices
                # only if you are superuser.
            return 'You do not have permission to archive this notice.'
        return None

    return _action(request, noticeid=noticeid, next_page=next_page, action=_archive)

@login_required
def delete(request, noticeid=None, next_page=None):
    def _delete(notice):
        if request.user == notice.user or request.user.is_superuser:
            notice.delete()
        else:   # you can delete other users' notices
                # only if you are superuser.
            return 'You do not have permission to delete this notice.'
        return None

    return _action(request, noticeid=noticeid, next_page=next_page, action=_delete)

@login_required
def mark_seen(request, noticeid=None, next_page=None):
    def _mark_seen(notice):
        if request.user == notice.user or request.user.is_superuser:
            notice.unseen = False
            notice.save()
        else:   # you can mark other users' notices as seen
                # only if you are superuser.
            return 'You do not have permission to mark this notice as seen.'
        return None

    return _action(request, noticeid=noticeid, next_page=next_page, action=_mark_seen)

@login_required
def mark_all_seen(request):
    for notice in Notice.objects.notices_for(request.user, unseen=True):
        notice.unseen = False
        notice.save()
    return HttpResponseRedirect(reverse("notification_notices"))
    