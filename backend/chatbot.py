import os
import openai
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import logging
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')

# System prompt for the chatbot
SYSTEM_PROMPT = """You are an advanced accounting assistant for a business accounting software. 
You can help with:

1. Creating and managing accounts
   - Setting up chart of accounts
   - Managing account groups and categories
   - Account reconciliation

2. Recording transactions and vouchers
   - Sales and purchase entries
   - Journal entries
   - Payment and receipt vouchers
   - Bank reconciliation

3. Generating financial reports
   - Balance Sheet
   - Profit & Loss Statement
   - Cash Flow Statement
   - Trial Balance
   - GST reports

4. GST compliance and reporting
   - GST registration
   - GST return filing
   - Input tax credit
   - GST audit

5. General accounting queries
   - Accounting principles
   - Tax compliance
   - Financial analysis
   - Budgeting and forecasting

Please provide clear, concise, and accurate responses. If you're unsure about something, acknowledge the limitation and suggest consulting a professional accountant."""

# Rate limiting settings
RATE_LIMIT = 50  # requests per hour
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds

def get_rate_limit_key(user_id):
    return f"chatbot_rate_limit:{user_id}"

def check_rate_limit(user_id):
    key = get_rate_limit_key(user_id)
    current_count = cache.get(key, 0)
    
    if current_count >= RATE_LIMIT:
        return False
    
    cache.set(key, current_count + 1, RATE_LIMIT_WINDOW)
    return True

@api_view(['POST'])
def chatbot(request):
    try:
        message = request.data.get('message')
        if not message:
            return Response(
                {'error': 'Message is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get user ID from request (you might want to implement proper user authentication)
        user_id = request.user.id if hasattr(request, 'user') else 'anonymous'
        
        # Check rate limit
        if not check_rate_limit(user_id):
            return Response(
                {'error': 'Rate limit exceeded. Please try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Log the incoming message
        logger.info(f"Received message from user {user_id}: {message}")

        # Get conversation history from cache
        history_key = f"chatbot_history:{user_id}"
        conversation_history = cache.get(history_key, [])
        
        # Prepare messages for OpenAI
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *conversation_history[-5:],  # Keep last 5 messages for context
            {"role": "user", "content": message}
        ]

        # Get response from OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=250
        )

        # Extract the response text
        bot_response = response.choices[0].message.content

        # Update conversation history
        conversation_history.extend([
            {"role": "user", "content": message},
            {"role": "assistant", "content": bot_response}
        ])
        cache.set(history_key, conversation_history, 3600)  # Store for 1 hour

        # Log the response
        logger.info(f"Bot response to user {user_id}: {bot_response}")

        return Response({'response': bot_response})

    except openai.error.AuthenticationError:
        logger.error("OpenAI API key is invalid or missing")
        return Response(
            {'error': 'AI service configuration error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except openai.error.RateLimitError:
        logger.error("OpenAI API rate limit exceeded")
        return Response(
            {'error': 'AI service is currently busy. Please try again later.'},
            status=status.HTTP_429_TOO_MANY_REQUESTS
        )
    except openai.error.InvalidRequestError as e:
        logger.error(f"Invalid request to OpenAI API: {str(e)}")
        return Response(
            {'error': 'Invalid request to AI service'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except openai.error.APIConnectionError:
        logger.error("Failed to connect to OpenAI API")
        return Response(
            {'error': 'Unable to connect to AI service. Please check your internet connection.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except Exception as e:
        logger.error(f"Unexpected error in chatbot: {str(e)}")
        return Response(
            {'error': 'An unexpected error occurred. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        ) 