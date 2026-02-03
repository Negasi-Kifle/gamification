from django.db import connection
from django.http import JsonResponse


def health_check(request):
    """
    Health check endpoint for deployment readiness.

    Returns:
        JSON response with health status and optional DB connectivity check.
    """
    health_status = {
        "status": "healthy",
        "service": "bonus",
    }

    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status["database"] = "connected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = "disconnected"
        health_status["error"] = str(e)
        return JsonResponse(health_status, status=503)

    return JsonResponse(health_status)
