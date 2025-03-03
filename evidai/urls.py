from django.contrib import admin
from django.urls import path
from evidai_chat import views

urlpatterns = [
    path('',views.hello_world,name='hello_world'),
    path('create_chat_session',views.create_chat_session,name='create_chat_session'),
    path('get_conversations',views.get_conversations,name='get_conversations'),
    path('evidAI_chat',views.evidAI_chat,name='evidAI_chat'),
    path('delete_chat_session',views.delete_chat_session,name='delete_chat_session'),
    path('get_chat_session_details',views.get_chat_session_details,name='get_chat_session_details'),
    path('update_prompt_values',views.update_prompt_values,name='update_prompt_values'),
    path('login',views.login,name='login'),
    path('add_prompt_values',views.add_prompt_values,name='add_prompt_values')
]
