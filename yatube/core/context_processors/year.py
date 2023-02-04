from django.utils.timezone import localdate


def year(request):
    """Добавляет переменную с текущим годом."""
    return {
        'year': localdate().year
    }
