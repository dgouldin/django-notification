from notification.models import Notice

def notification(request):
    if request.user.is_authenticated():
        return {
            'notice_unseen_count': Notice.objects.unseen_count_for(request.user, on_site=True),
            'notices': Notice.objects.notices_for(request.user, on_site=True),
        }
    else:
        return {}
