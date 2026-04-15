import os
from datetime import datetime
from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse


def get_error_info(request):
    return {
        "path": request.path,
        "method": request.method,
        "user": str(request.user) if request.user.is_authenticated else "Anonymous",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def bad_request(request, exception=None):
    if settings.DEBUG:
        error_info = get_error_info(request)
        return render(
            request,
            "errors/error.html",
            {
                "code": 400,
                "error_info": f"Requisição inválida: {request.path}",
                "timestamp": error_info["timestamp"],
            },
            status=400,
        )
    return HttpResponse("Página não encontrada", status=400)


def permission_denied(request, exception=None):
    if settings.DEBUG:
        error_info = get_error_info(request)
        return render(
            request,
            "errors/error.html",
            {
                "code": 403,
                "error_info": f"Acesso negado: {request.path}",
                "timestamp": error_info["timestamp"],
            },
            status=403,
        )
    return HttpResponse("Acesso negado", status=403)


def page_not_found(request, exception=None):
    if settings.DEBUG:
        error_info = get_error_info(request)
        return render(
            request,
            "errors/error.html",
            {
                "code": 404,
                "error_info": f"Página não encontrada: {request.path}",
                "timestamp": error_info["timestamp"],
            },
            status=404,
        )
    return HttpResponse("Página não encontrada", status=404)


def server_error(request):
    if not settings.DEBUG:
        try:
            from django.core.mail import send_mail

            error_info = get_error_info(request)
            send_mail(
                f"[7Event Error] 500 - {error_info['path']}",
                f"Path: {error_info['path']}\nUser: {error_info['user']}\nTimestamp: {error_info['timestamp']}",
                settings.DEFAULT_FROM_EMAIL,
                [getattr(settings, "ERROR_REPORT_EMAIL", "contato@7event.com.br")],
                fail_silently=True,
            )
        except Exception:
            pass
        return HttpResponse("Erro interno", status=500)

    error_info = get_error_info(request)
    return render(
        request,
        "errors/error.html",
        {
            "code": 500,
            "error_info": "Erro interno do servidor",
            "timestamp": error_info["timestamp"],
        },
        status=500,
    )
