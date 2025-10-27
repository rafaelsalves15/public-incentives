from .incentives import router as incentives_router
from .companies import router as companies_router
from .data_management import router as data_management_router
from .chatbot import router as chatbot_router
from .web_interface import router as web_interface_router

__all__ = ["incentives_router", "companies_router", "data_management_router", "chatbot_router", "web_interface_router"]
