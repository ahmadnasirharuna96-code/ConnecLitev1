from django.urls import path

from .views import ConversationListView, MessageListCreateView, SendMessageView

app_name = "messaging"

urlpatterns = [
    path("conversations/", ConversationListView.as_view(), name="conversation-list"),
    path("conversations/<uuid:conversation_id>/messages/", MessageListCreateView.as_view(), name="message-list"),
    path("messages/", SendMessageView.as_view(), name="send-message"),
]
