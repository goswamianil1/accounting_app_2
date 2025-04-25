import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger('core.auth')

def custom_exception_handler(exc, context):
    """Custom exception handler for better error messages."""
    response = exception_handler(exc, context)

    if response is None:
        if isinstance(exc, ValidationError):
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {'detail': 'A server error occurred.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    if isinstance(exc, (InvalidToken, TokenError)):
        logger.warning(f"Token validation failed: {str(exc)}")
        response.data = {'detail': 'Invalid token or token expired.'}
        return response

    # Log the error
    logger.error(f"Error occurred: {str(exc)}", exc_info=True)

    # Standardize the error response format
    if isinstance(response.data, dict):
        if 'detail' not in response.data:
            response.data = {'detail': str(response.data)}
    else:
        response.data = {'detail': str(response.data)}

    return response 