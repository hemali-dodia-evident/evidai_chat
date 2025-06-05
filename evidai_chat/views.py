import google.generativeai as genai
import os
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import datetime,timezone
from . import models
import logging
import requests
from . import chat_flow as cf
# from evidai_chat.qdrant import search_assets_by_question as sa

# def get_asset_list(db_alias):
#     asset_names = models.Asset.objects.using(db_alias).exclude(visibility='PRIVATE').values_list('name',flat=True)
#     return asset_names

# assets = ['tell me about tesla','how i can invest in dnd small cap fund?', 'what is openai',"is there any updates available on isro",'how many investors are there in open-ai', 'provide me more details on MSC Cruises']
# asset_names  = get_asset_list('prod')
# asset_names = list(asset_names)
# print(", ".join(asset_names))
# for ass in assets:
#     print(datetime.now())
#     res = sa.search_assets(ass)
#     print(res)
#     print(datetime.now())
#     print("******************")

key = os.environ["GOOGLE_API_KEY"]
genai.configure(api_key=f"{key}")

asset_verticals = {1:'Private Equity',2:'Venture Capital',3:'Private Credit',4:'Infrastructure',5:'Hedge Funds',6:'Digital Assets',
                    7:'Real Estate',8:'Collectibles'}

# Configure the logging settings
logger = logging.getLogger(__name__)

# Model response restriction
generation_config = {
    "temperature": 0.5,  # Lower randomness
    "top_p": 0.8  # Nucleus sampling
}


general_guidelines = """Response Guidelines:
You are smart and intelligent bot having knowledge of Finance sector. You can understand user's question and respond them with required information. You are very friendly and kind.
You are very friendly and helpful smart assistant. You have to provide only those information for which user is asking. And guide user just like you will guide your friend.
If an answer is fully available: Provide a clear, concise response with proper structure and formatting, considering answer's readability, line breaks, points everything.
If some information is unavailable but the rest is available: Mention that the specific missing information is unavailable. If needed, suggest contacting support.
If no relevant information is available then inform user in politely and friendly way that currently we dont have that information but they can approach support team for more clarity.
Support team contact -  support@evident.capital
Ask user to visit "Marketplace" for more details related to this asset and other asset if required.
Do not suggest or provide any recommendations, advice, or actions that may violate the rules, regulations, or guidelines set by the Securities and Futures Commission (SFC) and VARA. Ensure that all information and responses remain fully compliant with applicable laws and regulatory standards.
"""


# Test API
def hello_world(request):
    return JsonResponse({"message":"Request received successfully","data":[],"status":True},status=200)


# Get response from gemini
@csrf_exempt 
def get_gemini_response(question,prompt):
    try:
        # prompt = "Your name is EvidAI a smart intelligent bot of Evident LLP. You provide customer support and help them."+ prompt
        model = genai.GenerativeModel('gemini-2.0-flash')
        response_content = model.generate_content([prompt, question])
        return response_content.text.strip()
    except Exception as e:
        logger.error(f'Failed to get answer from gemini due to - {str(e)}')
        response = "Sorry! I am not able to find answer for your question. \nRequest you to coordinate with our support team on - support@evident.capital.\nThank You."
        return response


# Authenticate from jwt token we are getting from UI
@csrf_exempt
def token_validation(token,URL):
    # print(datetime.now())
    try:
        
        # Get User details
        url = f"https://{URL}/user/me"

        payload = {
                    "code": "123456",
                    "ipAddress":"127.0.0.1"
                }
        headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }

        response = requests.request("GET", url, headers=headers, data=payload)
        data = response.json()
        # print(datetime.now())
        # logger.info(f"token data - {data}")
        validate = data["user"]["twoFactorAuthenticationSession"]
        user_id = data["user"]["id"]
        user_name = data['user']['kyc']['fullName'].split()[0] if data['user']['kyc']['fullName'] != '' else ''
        user_role = 'Individual Investor'
        isAR = None
        
        if data['user']['isDistributor']==True:
            user_role = 'Distributor'            
        elif data['user']['isOwner']==True:
            user_role = 'Issuer'
        elif data['user']['isDistributor']==False and data['user']['isOwner']==False and data['user']['profile']['isInstitutional']==True:
            user_role = 'Corp Investor'
            isAR = data['user']['profile']['isAuthorizedRepresentative']
            
        onboarding_details = data['user']['individualOnboarding']
        onboarding_steps = ""
        for stp in onboarding_details:
            step_name = stp['stepName'].replace("_"," ")
            step_name = step_name[0].upper()+step_name[1:]
            step_status = stp['stepStatus'][0]+stp['stepStatus'][1:].lower()

            temp_stp = f"{step_name}:{step_status}"
            if onboarding_steps != '':
                onboarding_steps=onboarding_steps+'\n'+temp_stp    
            else:
                onboarding_steps=temp_stp
        isPI = data["user"]["investmentExperience"]["isProfessionalInvestor"]
        # print(datetime.now())
        
        if validate:
            return token, user_id, user_name, user_role, onboarding_steps, isAR, isPI
        else:
            return token, user_id, None, None, None, None

    except Exception as e:
        logger.error(f"Failed to get user/me response due to - {str(e)}")
        return token, None, None, None, None, None


# Add conversation to DB
@csrf_exempt
def add_to_conversations(db_alias, user_id, chat_session_id, current_question, response, current_asset, current_ques_cat):
    try:
        # Get the current date and time in UTC
        current_datetime = datetime.now(timezone.utc)

        # Convert to ISO 8601 format
        iso_format_datetime = current_datetime.isoformat()
        new_conv = models.Conversation.objects.using(db_alias).create(
            user_id=user_id,
            chat_session_id=chat_session_id,
            question=current_question,
            answer=response,
            created_at=iso_format_datetime,
            updated_at=iso_format_datetime,
            is_asset=current_asset,
            last_ques_cat=current_ques_cat
        )
        new_conv.save()
        return new_conv.id  
    except Exception as e:
        logger.error(f'Failed to add conversation for user_id={user_id}, chat_session_is={chat_session_id},question={current_asset},and answer={response} due to - '+str(e))
        return None  


# Get previous conversation as context
def get_contextual_input(conversation_history, max_length=1000):
    contextual_input = '\n'.join(set(f"User_Question: {entry['question']}" for entry in conversation_history))
    return contextual_input[-max_length:]


# Get all chat session based on user
@csrf_exempt
def get_chat_session_details(request):
    if request.method == 'GET':
        env = request.headers.get('X-Environment', 'uat').lower()
        db_alias = 'prod' if 'prod' in env else 'default'
        URL = os.getenv('URL') if 'prod' in env else os.getenv('UAT_URL')
        logger.info(f"get chat session db_alias - {db_alias}\n URL - {URL}")
        token = None
        # Extract the Bearer token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({"message":"missing header, please pass authentication token","data":{"response":"No authentication token present"},"status":False},status=200)
        
        # Get the token and validate it
        token = auth_header.split(' ')[1]
        token_valid,user_id,*extra = token_validation(token,URL)
        del extra
        if token_valid is None:
            logger.error(f"Invalid Token, Token: {token}")            
            return JsonResponse({"message":"Invalid user, please login again","data":{"response":"Failed to validate token for user, please check token"},"status":False},status=400) 
        try:
            chats = models.ChatSession.objects.using(db_alias).filter(user_id=user_id,show=True).order_by('-id')
            convos = []
            
            for chat in chats:  # Iterate over each ChatSession object in the QuerySet
                all_convo = {}
                all_convo["id"] = chat.id
                all_convo["title"] = chat.title  # Access the 'title' field of each chat
                convos.append(all_convo)
            return JsonResponse({"message":"All chat sessions fetched successfully",
                                "data":{"response":convos},"status":True},status=200)
        except Exception as e:
            logger.error(f"No chat sessions found - {str(e)}")
            return JsonResponse({"message":"No chat sessions found",
                                "data":{"response":[]},"status":True},status=400)
    else:
        return JsonResponse({
            "message": "Invalid JSON format",
            "status": False,
            "data": {"response":[]}
        }, status=400)


# Create Session
@csrf_exempt 
def create_chat_session(request):
    try:
        if request.method=='POST':
            env = request.headers.get('X-Environment', 'uat').lower()
            db_alias = 'prod' if 'prod' in env else 'default'
            URL = os.getenv('URL') if 'prod' in env else os.getenv('UAT_URL')
            logger.info(f"db_alias in create chat session - {db_alias}\nURL - {URL}")
            
            token = None
            # Extract the Bearer token from the Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({"message":"missing header, please pass authentication token","data":{"response":"No authentication token present"},"status":False},status=400)
            
            # Get the token and validate it
            token = auth_header.split(' ')[1]
            token_valid,user_id,*extra = token_validation(token,URL)
            del extra
            # print(token)
            if token_valid is None:
                logger.error(f"Invalid Token, Token: {token}")            
                return JsonResponse({"message":"Invalid user, please login again","data":{"response":"Failed to validate token for user, please check token"},"status":False},status=400)
            
            # Get the current date and time in UTC
            current_datetime = datetime.now(timezone.utc)

            # Convert to ISO 8601 format
            iso_format_datetime = current_datetime.isoformat()
            try:
                # Create a new ChatSession instance
                new_chat_session = models.ChatSession.objects.using(db_alias).create(
                    user_id=user_id,
                    title="New Conversation",
                    created_at=iso_format_datetime,
                    updated_at=iso_format_datetime
                )
                new_chat_session.save()
                return JsonResponse({
                'message': 'Response generated successfully',
                'status': True,
                'data': {
                    'response':'Chat session created successfully',
                    'id': new_chat_session.id,
                    'user_id': new_chat_session.user_id,
                    'title': new_chat_session.title,
                    'created_at': new_chat_session.created_at,
                    'updated_at': new_chat_session.updated_at,
                }
            }, status=200)
            except Exception as e:
                return JsonResponse({
                    "message": f"Failed to create chatsession due to - {e}",
                    "status": False,
                    "data": {"response":''}
                }, status=400)
            # Return a success response
            
        logger.info("New chat session created successfully")
    except json.JSONDecodeError:
        logger.error('Invalid JSON format while creating new chat session')
        return JsonResponse({
            "message": "Invalid JSON format",
            "status": False,
            "data": {"response":''}
        }, status=400)
    

# Update title of newly created chat session
@csrf_exempt
def update_chat_title(question,chat_session_id,db_alias):
    prompt = """Based on this question generate title for this conversation. 
    Title should be short, in context of question, and it should have 30 characters maximum. 
    Use proper formatting to enhance readability. DO NOT MENTIONE ANYTHING LIKE 'Short & Sweet: ...', Only generate title in context of conversatoin"""
    # Get the current date and time in UTC
    current_datetime = datetime.now(timezone.utc)

    # Convert to ISO 8601 format
    iso_format_datetime = current_datetime.isoformat()
    title = get_gemini_response(question,prompt)
    title = title.replace("*","")
    try:
        chat_session = models.ChatSession.objects.using(db_alias).get(id=chat_session_id)
        chat_session.title = title
        chat_session.updated_at = iso_format_datetime
        chat_session.save()
        logger.info(f"Title updated successfully for chat_session_id - {chat_session_id}")
    except Exception as e:
        logger.error(f"Failed to update title for chat_session_id - {chat_session_id} Due to - {str(e)}")
        title = "Current Conversation"
    return title


# Get question, answer, last asste, and last question category from conversation table in desc order(newest will be on top)
def get_conv_details(chat_session_id,db_alias):
    all_convo = models.Conversation.objects.using(db_alias).filter(chat_session_id=chat_session_id).order_by('-id')
    previous_questions = [q.question for q in all_convo]
    if len(previous_questions)>0:
        last_asset = all_convo[0].is_asset
        last_ques_cat = all_convo[0].last_ques_cat  
    else:
        last_ques_cat = ''
        last_asset = '' 
    return previous_questions, last_asset, last_ques_cat


# Get all conversation details
@csrf_exempt 
def get_conversations(request):
    if request.method == 'POST':
        token = None
        # Extract the Bearer token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({"message":"missing header, please pass authentication token","data":{"response":"No authentication token present"},"status":False},status=400)
        env = request.headers.get('X-Environment', 'uat').lower()
        db_alias = 'prod' if 'prod' in env else 'default'
        URL = os.getenv('URL') if 'prod' in env else os.getenv('UAT_URL')
        # Get the token and validate it
        token = auth_header.split(' ')[1]
        token_valid,*extra = token_validation(token,URL)
        del extra
        if token_valid is None:
            logger.error(f"Invalid Token, Token: {token}")            
            return JsonResponse({"message":"Invalid user, please login again","data":{"response":"Failed to validate token for user, please check token"},"status":False},status=400)
            
        data = json.loads(request.body)
        chat_session_id=data.get('chat_session_id')
        chat_present = models.ChatSession.objects.using(db_alias).get(id=chat_session_id)
        if chat_present.show ==True:
            try:
                all_convo = models.Conversation.objects.using(db_alias).filter(chat_session_id=chat_session_id).order_by('-id')
                convo_list = [
                    {"id": convo.id, "chat_session_id": convo.chat_session_id, "question": convo.question,
                    "answer":convo.answer, "created_at":convo.created_at,"updated_at":convo.updated_at}
                    for convo in all_convo
                ]
                # Construct the JSON response
                response_data = {
                    "message": "Response generated successfully",
                    "status": True,
                    "data": {
                        "response":convo_list
                    }
                }
                logger.info(f'conversations fetched successfully for chat session id - {chat_session_id}')
                return JsonResponse(response_data,status=200)
            except Exception as e:
                logger.error(f'failed to fetch conversations for chat session id - {chat_session_id} due to - {str(e)}')
                return JsonResponse({"message": "Unexpected error occurred.",
                    "status": False,
                    "data": {
                        "response":f"Unable to get Conversations due to - {str(e)}, Please try again."
                    }},status=400)
        else:
            logger.error(f'failed to fetch conversations for chat session id - {chat_session_id}')
            return JsonResponse({
                "message":"Failed to get conversations",
                "data":{"response":"Failed to get conversation details, please check if correct chat session id is passed."},
                "status":False
            },status=400)
    else:
        logger.error(f'failed to fetch conversations for chat session id - {chat_session_id}')
        return JsonResponse({
            "message": "Unexpected error occurred.",
            "status": False,
            "data": {'response':'Invalid method, POST method is expected'}
        }, status=400)


# Validate chat session id if it is active or not
def validate_chat_session(chat_session_id,db_alias):
    try:
        chat_session = models.ChatSession.objects.using(db_alias).get(id=int(chat_session_id))
        return chat_session
    except Exception as e:
        logger.error( f"Failed to validate chat session id - {chat_session_id} due to - {str(e)}")
        return 


# Delete Chat session
@csrf_exempt
def delete_chat_session(request):
    if request.method=="POST":
        token = None
        # Extract the Bearer token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({"message":"missing header, please pass authentication token","data":{"response":"No authentication token present"},"status":False},status=400)
        env = request.headers.get('X-Environment', 'uat').lower()
        db_alias = 'prod' if 'prod' in env else 'default'
        URL = os.getenv('URL') if 'prod' in env else os.getenv('UAT_URL')
        logger.info(f"Delete chat session db_alias - {db_alias}\nURL - {URL}")
        # Get the token and validate it
        token = auth_header.split(' ')[1]
        token_valid,*extra = token_validation(token,URL)
        del extra
        if token_valid is None:
            logger.error("error",f"Invalid Token, Token: {token}")            
            return JsonResponse({"message":"Invalid user, please login again","data":{"response":"Failed to validate token for user, please check token"},"status":False},status=400)
            
        data = json.loads(request.body)
        chat_session_id = data.get("chat_session_id")
        try:
            chat = models.ChatSession.objects.using(db_alias).get(id=chat_session_id)
            chat.show = False
            chat.save()
            logger.info(f"deleted chat session id - {chat_session_id} successfully")
            return JsonResponse({"message":"Chat session deleted successfully","data":{
            "chat_session_id":chat_session_id, "title":chat.title},"status":True},status=200)
        except Exception as e:
            logger.error( f"Failed to delete chat session id - {chat_session_id} due to - {str(e)}")
            return JsonResponse({"message":"Failed to delete Chat session","data":{"response":"Please check if correct chat session id is passed."},"status":False},status=400)
    else:
        logger.error(f"Failed to delete chat session id - {chat_session_id} due to - {str(e)}")
        return JsonResponse({"message":"Invalid request type, POST method is expected","data":{'response':''},"status":False},status=400)


# @csrf_exempt
def login(request):
    # print("in login")
    url = f"https://api-uat.evident.capital/user/login"
    payload = json.dumps({
    # "email": "shwetac0106@yopmail.com",
    "email": "rahul0606+@ind.com",
    "password": "Evident@2025",
    "ipInfo": {
        "asn": "asn",
        "asnName": "asnName",
        "countryName": "India",
        "ip": "127.0.0.1",
        "isEu": False,
        "latitude": "30.3456",
        "longitude": "30.3456",
        "isAnonymous": False,
        "isBogon": False,
        "isDatacenter": False,
        "isIcloudRelay": False,
        "isKnownAbuser": False,
        "isKnownAttacker": False,
        "isProxy": False,
        "isThreat": False,
        "isTor": False
    }
    })
    headers = {
    'Content-Type': 'application/json',
    'Origin': 'https://test.evident.capital'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    data = response.json()
    logger.info(f"login response - {data}")
    token = data['token']
    return JsonResponse({"token":token},status=200)


# Main flow
@csrf_exempt
def evidAI_chat(request):
    try:
        if request.method == 'POST':
            logger.info(f"request url - {request.get_host()}")
            token = None
            # Extract the Bearer token from the Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({"message":"missing header, please pass authentication token","data":{"response":"No authentication token present"},"status":False},status=400)

            env = request.headers.get('X-Environment', 'uat').lower()
            db_alias = 'prod' if 'prod' in env else 'default'
            URL = os.getenv('URL') if 'prod' in env else os.getenv('UAT_URL')
            logger.info(f"db_alias - {db_alias}\nURL - {URL}")
            # Get the token and validate it
            token = auth_header.split(' ')[1]
            # Token validation takes almost 2.5 to 3 seconds
            token_valid,user_id,user_name,user_role,onboarding_step,isAR,isPI = token_validation(token,URL)
            logger.info(f"user_id - {user_id}")
            if token_valid is None:
                logger.error(f"Invalid Token, Token: {token}")            
                return JsonResponse({"message":"Invalid user, please login again","data":{"response":"Failed to validate token for user, please check token"},"status":False},status=400)
            
            data = json.loads(request.body)
            current_question = data.get('question')
            chat_session_id = int(data.get('chat_session_id'))

            # chat session validation
            chat_session_validation = validate_chat_session(chat_session_id,db_alias)
            if chat_session_validation is None:
                logger.error(f'Invalid chat session, kindly create new chat session for user ID - {user_id}')
                return JsonResponse({"message":"Unexpected error occured","data":{
                "response":"Invalid chat session, kindly create new chat session"},"status":False},status=200)
            
            previous_questions, last_asset, last_ques_cat = get_conv_details(chat_session_id,db_alias)

            # Update title
            if len(previous_questions)==1:
                update_chat_title(current_question,chat_session_id,db_alias)
                
            response, current_asset, current_ques_cat = cf.handle_questions(URL,db_alias,token, last_asset, last_ques_cat, user_name, user_role, current_question, onboarding_step, isAR, isPI)
            response = response.replace("\n", "  \n")  
            add_to_conversations(db_alias,user_id, chat_session_id, current_question, response, current_asset, current_ques_cat)      
            
            return JsonResponse({"message":"Response generated successfully","data":{
                                    "response":response},"status":True},status=200)
        
        else:
            logger.error('Invalid method request, POST method is expected.')
            return JsonResponse({"message":"Unexpected error occurred","data":{
                "response":"Invalid method request, POST method is expected."},"status":False},status=400)
    except Exception as e:
        logger.error(f"Error occured from main function - {str(e)}")
        return JsonResponse({"message":"Unexpected error occured","data":{
                "response":f'{str(e)}'},"status":False},status=400)


@csrf_exempt
def update_prompt_values(request):
    if request.method=='POST':
        try:
            data = json.loads(request.body)
            value = data['value']
            category = data['category'].replace("_"," ")
            env = request.headers.get('X-Environment', 'uat').lower()
            db_alias = 'prod' if 'prod' in env else 'default'
            prompt_table = models.BasicPrompts.objects.using(db_alias).get(prompt_category=category)
            prompt_table.prompt = value
            prompt_table.save()

            prompt_table = models.BasicPrompts.objects.using(db_alias).get(prompt_category=category)
            value = prompt_table.prompt
            return JsonResponse({"message":"Value updated successfully","data":{"updated_prompt":value},"status":True},status=200)
        except Exception as e:
            return JsonResponse({"message":"Failed to update prompt","data":{"error":str(e)},"status":False},status=400)


@csrf_exempt
def add_prompt_values(request):
    if request.method=='POST':
        try:
            # Get the current date and time in UTC
            current_datetime = datetime.now(timezone.utc)
            data = json.loads(request.body)
            value = data['value']
            category = data['category'].replace("_"," ")
            asset_name = data['asset_name']
            asset_sub_cat = data['asset_sub_cat']
            prm_id = data['id']
            # Convert to ISO 8601 format
            iso_format_datetime = current_datetime.isoformat()
            env = request.headers.get('X-Environment', 'uat').lower()
            db_alias = 'prod' if 'prod' in env else 'default'
            new_cat = models.BasicPrompts.objects.using(db_alias).create(
                id=prm_id,
                prompt_category=category,
                prompt=value,
                asset_name=asset_name,
                asset_sub_cat=asset_sub_cat,
                created_at=iso_format_datetime,
                updated_at=iso_format_datetime               
            )
            new_cat.save()
            return JsonResponse({"message":"Value added successfully",
                                 "data":{"prompt_category":category,'prompt':value,
                                         "asset_name":asset_name,"asset_sub_cat":asset_sub_cat},"status":True},status=200) 
        except Exception as e:
            return JsonResponse({"message":"Failed to add prompt","data":{"error":str(e)},"status":False},status=400)


@csrf_exempt
def delete_prompt_value(request):
    if request.method=='POST':
        try:
            env = request.headers.get('X-Environment', 'uat').lower()
            db_alias = 'prod' if 'prod' in env else 'default'

            data = json.loads(request.body)
            prompt_id = data.get('id')  # Get ID from request body
            
            # Check if the object exists
            prompt = models.BasicPrompts.objects.using(db_alias).get(id=prompt_id)
            prompt.delete()  # Delete the object
            
            return JsonResponse({"message": "Deleted successfully"}, status=200)
        except models.BasicPrompts.DoesNotExist:
            return JsonResponse({"error": "Prompt not found"}, status=404)


@csrf_exempt
def get_prompt_id(request):
    if request.method=='POST':
        try:
            data = json.loads(request.body)
            category = data['category'].replace("_"," ")
            env = request.headers.get('X-Environment', 'uat').lower()
            db_alias = 'prod' if 'prod' in env else 'default'
            prompt_table = models.BasicPrompts.objects.using(db_alias).filter(prompt_category=category).values_list('id',flat=True)
            prompt_id = list(prompt_table)

            return JsonResponse({"message":"ID fetched successfully","data":{"IDs":prompt_id},"status":True},status=200)
        except Exception as e:
            return JsonResponse({"message":"Failed to get prompt id","data":{"error":str(e)},"status":False},status=400)


@csrf_exempt
def get_all_prompt_catogiries(request):
    if request.method=='POST':
        try:
            env = request.headers.get('X-Environment', 'uat').lower()
            db_alias = 'prod' if 'prod' in env else 'default'
            prompt_table = models.BasicPrompts.objects.using(db_alias).values_list('id','prompt_category','prompt')
            prompt_id = list(prompt_table)
            logger.info(f"Available Prompts - {prompt_table}")
            return JsonResponse({"message":"ID fetched successfully","data":{"IDs":prompt_id},"status":True},status=200)
        except Exception as e:
            return JsonResponse({"message":"Failed to get prompt categories","data":{"error":str(e)},"status":False},status=400)
