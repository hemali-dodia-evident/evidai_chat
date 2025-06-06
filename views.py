import google.generativeai as genai
import os
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import datetime,timezone
from . import models
import logging
from django.shortcuts import render
import markdown
import requests
import re


key = os.environ["GOOGLE_API_KEY"]
genai.configure(api_key=f"{key}")

asset_verticals = {1:'Private Equity',2:'Venture Capital',3:'Private Credit',4:'Infrastructure',5:'Hedge Funds',6:'Digital Assets',
                    7:'Real Estate',8:'Collectibles'}

# Configure the logging settings
logger = logging.getLogger(__name__)

# Model response restriction
generation_config = {
    "temperature": 0.1,  # Lower randomness
    "top_p": 0.8  # Nucleus sampling
}


# Test API
def hello_world(request):
    return JsonResponse({"message":"Request received successfully","data":[],"status":True},status=200)


# Get response from gemini
@csrf_exempt 
def get_gemini_response(question,prompt):
    try:
        # prompt = "Your name is EvidAI a smart intelligent bot of Evident LLP. You provide customer support and help them."+ prompt
        model = genai.GenerativeModel('gemini-1.5-pro')
        response_content = model.generate_content([prompt, question])
        return response_content.text.strip()
    except Exception as e:
        logger.error(f'Failed to get answer from gemini due to - {str(e)}')
        response = "Sorry! I am not able to find answer for your question. \nRequest you to coordinate with our support team on - support@evident.capital.\nThank You."
        return response


# Identify prompt category based on current and previous questions
def get_prompt_category(current_question,user_role,last_asset,last_ques_cat):
    # logger.info("Finding prompt from get_prompt_category")
    prompt = f"""Based on user's question identify the category of a question from below mentioned categories. STRICTLY PROVIDE ONLY NAME OF CATEGORIES NOTHING ELSE, IF NO CATEGORY MATCHES THEN RETURN "FAILED".
                 Note - While answering do not add any other information or words. Just reply as per specified way. ONLY PROVIDE ONLY NAME OF CATEGORIES. CONSIDER GENERIC ABRIAVATIONS IN CONTEXT OF QUESTION, LIKE 'CORP INV' WILL BE 'Corp Investor'.
                 USER's QUESTION - {current_question}
                 Last Asset about which user asked - {last_asset}
                 Last Question Category regarding which conversation was going on - {last_ques_cat}
                 USER's ROLE - {user_role}.
                 IF QUESTION IS ABOUT USER'S ONBOARDING OR PENDING STEPS OR QUERY ABOUT ANY STEP RELATED TO ONBOARDING THEN REFER "USER's ROLE" AND SELECT CATEGORY ACCORDINGLY, ALSO IF LAST QUESTION CATEGORY WAS RELATED TO "ONBOARDING" THEN SELECT PROPER ONBOARDING CATEGORY.
                 Greetings: USER IS GREETING WITHOUT ANY OTHER INFORMATION, Contains generic formal or friendly greetings like hi, hello, how are you, who are you, etc. It DOES NOT contain any other query related to below catrgories mentioned below.
                 Personal_Assets: Following details are present for variety of assets like openai, spacex and many more - These assets include various categories such as Private Equity, Venture Capital, 
                    Private Credit, Infrastructure, Hedge Funds, Digital Assets, Real Estate, Collectibles, 
                    Structuring, Private Company Debenture, Note, Bond, Fund, and Equity. 
                    These assets have a range of Internal Rate of Return i.e. IRR. 
                    The minimum investment amount varies in different ranges. 
                    Key tags associated with these assets include Commitment, Captain, Trading, Event Soon, 
                    Campaign Closing Soon, Exclusive, New, Tallulah Nash, Completed, Asset Exited, Trending, 
                    Commitment Ended, Coming Soon, and Commitment Ongoing. 
                    Only professional investors are eligible to invest in these assets, ensuring that the investment 
                    opportunities are restricted to a specific investor class. 
                    Complete details of assets, current status, investment, trade, structure, tags, etc. related to 
                    that asset, commitments. Here user asks about different things on asset, About manager, company etc.
                    These are user specific assets. When user wants to know about his/her asset details.
                    - Below are the key details present for each asset:  
                    - **General Information:**  
                    - Asset Name, Description, Location, Currency, Asset Code, Investment Mode, Structuring Type, Asset Vertical, Status, Status Tag, Visibility.  

                    - **Investment Details:**  
                    - Target Amount, Minimum Investment Amount, Raised Amount, Investment Start Date, Investment End Date, Open Offers, Number of Investors, Total Invested Amount.  

                    - **Exit & Performance Details:**  
                    - Rate of Return, Exit Strategy, Latest Ticker, Previous Ticker.  

                    - **Manager Information:**  
                    - Manager Name, Manager Email, Manager Nickname, Manager Avatar, Managing Company Name, Managing Company Logo, Managing Company Website.  
                    **Example queries:** 
                        - "Who is the manager of OpenAI?"
                        - "Tell me about manager"
                        - "Tell me about OpenAI."
                        - "What is OpenAI’s investment mode?"
                 Assets_Creation: Detailed process only to create assets. 
                 Asset_Managers:This category contains information about due diligence process for asset managers, the structuring and tokenization of assets, and the various fundraising methods available on the platform, emphasizing efficiency, transparency, and investor protection.
                 Onboarding_Distributor:Detailed process for distributor onboarding process.
                 Onboarding_Issuer:Detailed process for issuer onboarding process.
                 Forget_Password: Contains step by step process to change or update password.
                 Corp_Investor_Onboarding:Detailed process for Corp investor onboarding process. Can also be reffered as Corp Onboarding or in similar context.
                 Onboarding_Investor:Detailed process for investor onboarding process. Which contains following detailed steps - REGISTRATION, Verification -> Confirmed -> Declaration and terms, email confirmation, Screening questions,
                 Investment_Guide:Provides step by step process and guidance for investing in any asset.    
                 NOTE - IF MORE THAN ONE CATEGORY MATCHES THEN RETURN THEIR NAME WITH "," SEPERATED. 
                 - If user is talking or mentioning platform without specifying name of platform then it simply means Evident platform on which currently they are present. So refer all categories present above then provide answer.
                 E.g. Qestion: What are the steps for investor onboarding?
                      Bot: Onboarding_Investor, Corp_Investor_Onboarding
                      Question: can you give me details about buying tokenized assets?
                      Bot: buy_and_sell_tokenized_assets
                      Question: Tell me about openai
                      Bot: Personal_Assets
                      Question: Hey i want some help
                      Bot: Greetings
                    
                    - IF USER'S ROLE - Individual Investor
                      Question: What are my onboarding steps/What are my pending steps
                      Bot: Onboarding_Investor
                 """
    response = get_gemini_response(current_question,prompt)
    # logger.info(f"prompt category - {response}")
    return response


# Authenticate from jwt token we are getting from UI
@csrf_exempt
def token_validation(token):    
    try:
        
        # Get User details
        url = "https://api-uat.evident.capital/user/me"

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
        validate = data["user"]["twoFactorAuthenticationSession"]
        user_id = data["user"]["id"]
        user_name = data['user']['kyc']['fullName'].split()[0] if data['user']['kyc']['fullName'] != '' else ''
        user_role = 'Individual Investor'
        if data['user']['isDistributor']==True:
            user_role = 'Distributor'
        elif data['user']['isOwner']==True:
            user_role = 'Issuer'
        elif data['user']['isDistributor']==False and data['user']['isOwner']==False and data['user']['profile']['isInstitutional']==True:
            user_role = 'Corp Investor'
        onboarding_details = data['user']['individualOnboarding']
        onboarding_steps = []
        for stp in onboarding_details:
            temp_stp = {}
            temp_stp['stepName'] = stp['stepName']
            temp_stp['stepStatus'] = stp['stepStatus']     
            onboarding_steps.append(temp_stp)       
        
        if validate:
            return token, user_id, user_name, user_role, onboarding_steps
        else:
            return token, None, None, None, None

    except Exception as e:
        logger.error(f"Failed to get user/me response due to - {str(e)}")
        return token, '', '', '', ''


# Add conversation to DB
@csrf_exempt
def add_to_conversations(user_id, chat_session_id, current_question, response, current_asset, current_ques_cat):
    try:
        # Get the current date and time in UTC
        current_datetime = datetime.now(timezone.utc)

        # Convert to ISO 8601 format
        iso_format_datetime = current_datetime.isoformat()
        new_conv = models.Conversation.objects.create(
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
        token = None
        # Extract the Bearer token from the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JsonResponse({"message":"missing header, please pass authentication token","data":{"response":"No authentication token present"},"status":False},status=200)
        
        # Get the token and validate it
        token = auth_header.split(' ')[1]
        token_valid,user_id,*extra = token_validation(token)
        del extra
        if token_valid is None:
            logger.error(f"Invalid Token, Token: {token}")            
            return JsonResponse({"message":"Invalid user, please login again","data":{"response":"Failed to validate token for user, please check token"},"status":False},status=400) 
        try:
            chats = models.ChatSession.objects.filter(user_id=user_id,show=True).order_by('-id')
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
            token = None
            # Extract the Bearer token from the Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({"message":"missing header, please pass authentication token","data":{"response":"No authentication token present"},"status":False},status=400)
            
            # Get the token and validate it
            token = auth_header.split(' ')[1]
            token_valid,user_id,*extra = token_validation(token)
            del extra
            # print(token)
            if token_valid is None:
                logger.error(f"Invalid Token, Token: {token}")            
                return JsonResponse({"message":"Invalid user, please login again","data":{"response":"Failed to validate token for user, please check token"},"status":False},status=400)
                
            # Get the current date and time in UTC
            current_datetime = datetime.now(timezone.utc)

            # Convert to ISO 8601 format
            iso_format_datetime = current_datetime.isoformat()
            # Create a new ChatSession instance
            new_chat_session = models.ChatSession.objects.create(
                user_id=user_id,
                title="New Conversation",
                created_at=iso_format_datetime,
                updated_at=iso_format_datetime
            )
            new_chat_session.save()
            # Return a success response
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
def update_chat_title(question,chat_session_id):
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
        chat_session = models.ChatSession.objects.get(id=chat_session_id)
        chat_session.title = title
        chat_session.updated_at = iso_format_datetime
        chat_session.save()
        logger.info(f"Title updated successfully for chat_session_id - {chat_session_id}")
    except Exception as e:
        logger.error(f"Failed to update title for chat_session_id - {chat_session_id} Due to - {str(e)}")
        title = "Current Conversation"
    return title


# Get question, answer, last asste, and last question category from conversation table in desc order(newest will be on top)
def get_conv_details(chat_session_id):
    all_convo = models.Conversation.objects.filter(chat_session_id=chat_session_id).order_by('-id')
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
        
        # Get the token and validate it
        token = auth_header.split(' ')[1]
        token_valid,*extra = token_validation(token)
        del extra
        if token_valid is None:
            logger.error(f"Invalid Token, Token: {token}")            
            return JsonResponse({"message":"Invalid user, please login again","data":{"response":"Failed to validate token for user, please check token"},"status":False},status=400)
            
        data = json.loads(request.body)
    
        chat_session_id=data.get('chat_session_id')
        chat_present = models.ChatSession.objects.get(id=chat_session_id)
        if chat_present.show ==True:
            try:
                all_convo = models.Conversation.objects.filter(chat_session_id=chat_session_id).order_by('-id')
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
def validate_chat_session(chat_session_id):
    try:
        # print("chat_session_id - ",chat_session_id)
        chat_session = models.ChatSession.objects.get(id=int(chat_session_id))
        return chat_session
    except Exception as e:
        # print(str(e))
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
        
        # Get the token and validate it
        token = auth_header.split(' ')[1]
        token_valid,*extra = token_validation(token)
        del extra
        if token_valid is None:
            logger.error("error",f"Invalid Token, Token: {token}")            
            return JsonResponse({"message":"Invalid user, please login again","data":{"response":"Failed to validate token for user, please check token"},"status":False},status=400)
            
        data = json.loads(request.body)
        chat_session_id = data.get("chat_session_id")
        try:
            chat = models.ChatSession.objects.get(id=chat_session_id)
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


# Generate answer from internet
def search_on_internet(question):
    try:
        prompt = """You are smart and intelligent chat-bot having good knowledge of finance and investment sector considering this chat with user.
                    Provide answer in a way that you are chatting with customer. Do not use any kind of emojis.
                    Chat with user, provide all information you can, support them, resolve their queries if they have and 
                    inform that this information is from internet search. Be nice and sweet along with inteligent while chatting. 
                    If its greeting text then simply greet them and ask how you can help them. Keep asnwer to the point.
                    NOTE - Keep tone positive and polite while answering user's query.
                    Avoid mentioning or implying that the user has not provided information.
                    Do not greet the user in your response. If you are unable to find answer then just say "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at support@evident.capital with the details of your query, and they’ll assist you promptly."
                    Use proper formatting such as line breaks to enhance readability. Do NOT use any kind of formating like "*" just give proper line breaks using '\n'.
                    Maintain a positive and polite tone throughout the response.
                    The response should be clear, concise, and user-friendly, adhering to these guidelines.
                """
        response = get_gemini_response(question,prompt)
        logger.info(f"internet search response - {response}")
    except Exception as e:
        logger.error(f"search_on_internet - {str(e)}")
    return response


# Get user specific assets in which user has invested
def users_assets(token):
    url = "https://api-uat.evident.capital/investor/investment/transactions"
    payload = {}
    headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
    response = requests.request("GET", url, headers=headers, data=payload)
    data = response.json() 
    # print(data)
    trades = data['trades']
    # print(trades)
    trade_details = None
    if trades == []:
        trade_details = "No trade available"
    else:
        trade_details = ""
        for trd in trades:
            id = int(trd['assetId'])
            try:
                asset = models.Asset.objects.get(id=id)
                name = asset.name
            except:
                name = 'Not Available'
            
            assetMaker=trd['maker']['kyc']['firstName']+' '+trd['maker']['kyc']['lastName']
            temp = f"""Trade Asset:{name}\nPrice:{trd["price"]}\nTotal Units:{trd["totalUnits"]}\nAvailable Units:{trd["availableUnits"]}\nTrade Units:{trd['tradedUnits']}\nTrade Status:{trd['status']}\nNumber of Clients:{trd["numberOfClients"]}\nAsset Maker:{assetMaker}"""
            trade_details=trade_details+'\n'+temp

    commitments = data['commitments']
    commitment_details = None
    if commitments == []:
        commitment_details = "No commitments available"
    else:
        commitment_details = ""
        for commit in commitments:
            temp = f"""Asset Name:{commit['commitmentDetails']['asset']['name']}\nCommitment Amount:{commit['commitmentAmount']}\nAlloted Units:{commit['allotedUnits']}\nCommitment Status:{commit['status']}"""
            commitment_details = commitment_details +'\n'+temp
    my_assets = [trade_details,commitment_details]

    return my_assets


# users_assets('NTI4OQ.8mSh9ge4S6xpHA2a8k3RMsxo9-8otyPQMsg6bzqCq2K01BCp1VpbzEEi8ndw')

# Get list of all assets from DB
def get_asset_list():
    # asset_names = models.Asset.objects.exclude(visibility='PRIVATE').values_list('name',flat=True)
    asset_names = models.Asset.objects.values_list('name',flat=True)
    return asset_names


def safe_value(value):
    return value if value is not None else ""


# Check category of question and then based on category generate response
# IP Count:10, OP Count:3
def category_based_question(current_question,promp_cat,token,onboarding_step,isRelated,isAssetRelated,last_ques_cat,current_asset,isPersonalAsset):
    question = current_question
    final_response = ""
    asset_found = current_asset
    try:        
        promp_cat_new = ",".join(promp_cat)
        specific_category = promp_cat_new.replace("_",' ').split(',')
        assets_identified = ""
        personalAssets = isPersonalAsset 
        for promp_cat in specific_category:   
            logger.info(f"Getting answer for category - {promp_cat}")    
            if (promp_cat!='FAILED' and promp_cat !='Personal Assets'): 
                try:
                    categories = last_ques_cat.split(",")
                    categories.append(promp_cat)
                    data = models.BasicPrompts.objects.filter(prompt_category__in=categories)
                    prompt_data_list = []
                    for d in data:
                        prm = d.prompt
                        if 'Onboarding' in promp_cat:
                            prm = f"""{prm} \nONLY USE THIS INFORMATION IF REQUIRED TO ANSWER USER'S QUERY. IF USER IS NOT ASKING ABOUT PENDING STEP THEN DO NOT REFER BELOW INFORMATION.\nUser\'s current onboarding status - {onboarding_step}
                                    If user's any step is not having 'stepStatus' as 'COMPLETED' then ask user to Complete that step.
                                    NOTE - IF USER IS ASKING ABOUT ONLY ONBOARDING STEPS AND NOT ABOUT HIS PENDING ONBOARDING DETAILS THEN PROVIDE ONLY ONBOARDING STEPS. DO NOT ASK USER TO FINISH PENDING STEPS."""
                        prompt_data_list.append(prm)
                    # logger.info(prompt_data_list)
                    prompt_data = f"""Customer is not providing you any information, all information is with you, DO NOT SAY TO CUSTOMER THAT THEY HAVE NOT PROVIDED INFORMATION,INSTEAD SAY YOU DONT HAVE INFORMATION CURRENTLY ON THIS. You are smart and intelligent chat-bot having good knowledge of finance sector considering this chat with user. 
                    Provide answer in a way that you are chatting with customer. Do not use any kind of emojis. Do not greet user while answering. Guide and help user to finish their steps and complete onboarding. Use below information to get answer -
                    {prompt_data_list}
                    NOTE - If you are not able to find answer then say "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at support@evident.capital with the details of your query, and they’ll assist you promptly."
                    Keep tone positive and polite while answering user's query.
                    Avoid mentioning or implying that the user has not provided information.
                    Do not greet the user in your response. If you are unable to find answer then just say "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at support@evident.capital with the details of your query, and they’ll assist you promptly."
                    Use proper formatting such as line breaks to enhance readability. Do NOT use any kind of formating like "*" just give proper line breaks using '\n'.
                    Maintain a positive and polite tone throughout the response.
                    The response should be clear, concise, and user-friendly, adhering to these guidelines."""
                    response = get_gemini_response(question,prompt_data)
                    final_response = final_response + '\n' + response    
                except Exception as e:
                    logger.info(f"Failed to find general category related information in DB - {str(e)}")
                    prm = """For this topic currently we don't have any information. 
                    Provide answer in a way that "I’m sorry I couldn’t assist you right now. 
                    However, our support team would be delighted to help! Please don’t hesitate to email 
                    them at support@evident.capital with the details of your query, and they’ll assist you promptly." 
                    this will cover the part of question for which information is not available"""
                    final_response = get_gemini_response(question,prm)
            elif promp_cat=='FAILED':
                logger.info("Prompt Category is 'FAILED'")
                response = search_on_internet(question)
                final_response = final_response + '\n' + response   
            elif 'Personal Assets' in promp_cat or (isRelated==True and isAssetRelated==True) or isAssetRelated==True or personalAssets==True:    
                logger.info("Prompt Category is Personal Asset") 
                if personalAssets==True:
                    idx = specific_category.index(promp_cat)
                    specific_category[idx] = 'Owned Assets'
                    assets_identified = users_assets(token)                    
                    prompt = f"""Below are asset details in which user has invested. 
                    Understand user's question carefully and provide answer using below mentioned details. 
                    Answer should be clear, and in positive and polite tone. Make sure answer is readable. 
                    If you are unable to answer then ask user to visit - 'https://uat.investor.evident.capital/portfolio/assets'
                    User's Trade:-{assets_identified[0]}
                    User's Commitments:-{assets_identified[1]}

                    RESPONSE GUIDELINES(STRICT FORMAT):-
                    - FOR TRADES, STRICTLY FOLLOW THIS: DO NOT APPLY LINE BREAK BETWEEN "Price:" and its value, and "Trade Unit:" and its value.
                        **Trade Details:-** 
                         Trade Asset - XYZ
                         Price - 123.0
                         Total Units - 123456
                         Available Units - 0
                         Trade Units - 10.0
                         Trade Status - Complete
                         Number of Clients - 2
                         Asset Maker - Jon
                         ==========================
                         Trade Asset - ABC
                         Price - 456.0
                         Total Units - 126
                         Available Units - 0
                         Trade Units - 10.0
                         Trade Status - Pending
                         Number of Clients - 2
                         Asset Maker - Don
                         ==========================
                         Trade Asset - qwe
                         Price - 123.0
                         Total Units - 123456
                         Available Units- 0
                         Trade Units - 10.0
                         Trade Status - Failed
                         Number of Clients - 2
                         Asset Maker - Jon
                         ==========================
                    - FOR COMMITMENTS, STRICTLY FOLLOW THIS:
                        **Commitment Details:-**
                         Asset Name - asjhs oosidos,
                         Commitment Amount - 2000,
                         Allotted Units - 10,
                         Commitment Status - Completed 
                         ==========================
                         Asset Name - asjhs,
                         Commitment Amount - 500,
                         Allotted Units - 330,
                         Commitment Status - Completed

                    ### **IMPORTANT RULES:**  
                     **STRICTLY FOLLOW the RESPONSE GUIDELINES EXACTLY AS PROVIDED.** 
                     **DO NOT APPLY LINE BREAKS IF THERE IS NUMERIC VALUE IN STATEMENT 
                     **DO NOT APPLY any additional formatting (e.g., *, _, or markdown styling).**  
                     **DO NOT GREET the user in the response.**  
                     **KEEP the tone positive, polite, and user-friendly.**  
                     **DO NOT mention or imply that the user has not provided information.**  
                     **Ensure line breaks are only applied between different attributes, NOT within values.**  

                    FAILURE TO FOLLOW THIS RESPONSE FORMAT IS NOT ACCEPTABLE. STRICTLY ADHERE TO THE GUIDELINES."""
                    response = get_gemini_response(question,prompt)
                    final_response = final_response + '\n' + response   
                    personalAssets = False                
                else:
                    assets_identified = current_asset.split(",")
                    response = get_asset_based_response(assets_identified,question,token)
                    final_response = final_response + '\n' + response 
                    asset_found = ",".join(assets_identified)                 
            else:
                response = search_on_internet(question)
                final_response = final_response + '\n' + response  
        if final_response == "":
            final_response = "Sorry! I am unable understand the question. Can you provide more details so I can assist you better?"
        prompt = """Follow these instructions exactly to ensure a structured, clear, and user-friendly response:
                    Remove all repetitive statements while preserving essential information.
                    Maintain readability by structuring the response with appropriate line breaks.                    
                    Use formatting correctly:
                    If the response contains steps, ensure each step starts on a new line for proper formatting.
                    Keep a positive and polite tone while responding.
                    Never imply that the user has not provided information.
                    Response Guidelines:
                    If an answer is fully available: Provide a clear, concise response with proper structure and formatting.
                    If some information is unavailable but the rest is available: Mention that the specific missing information is unavailable. If needed, suggest contacting support:
                    "Certain details are unavailable, but our support team would be happy to assist you. Please reach out to support@evident.capital with your query."
                    If no relevant information is available: Respond with:
                    "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at support@evident.capital with the details of your query, and they’ll assist you promptly."
                    For more assistance or further assistance scenario provide support contact - support@evident.capital
                    Ensure:
                    The response is structured well with line breaks for readability.
                    Ensure line breaks are only applied between different attributes, or point, NOT within values.
                    The tone remains friendly and professional.
                    APPLY BOLD ONLY FOR HEADINGS, AND KEYS WHERE KEY-VALUE PAIR IS PRESENT.
                    Format the steps in a clear, structured, and readable format. 
                    Steps are properly formatted, with each step appearing on a new line.
                    No extra words, unnecessary greetings, or irrelevant details are added.
                    Do not include the full support message unless all information is unavailable.
                    Strictly follow these instructions to generate the best response."""
        if personalAssets==False:
            final_response = get_gemini_response(final_response,prompt)
        
        logger.info(f"Categories final - {specific_category}")
    except Exception as e:
        logger.error(f"While generating answer from category based question following error occured - {str(e)}")
        final_response = "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at support@evident.capital with the details of your query, and they’ll assist you promptly."
        
    return final_response, asset_found, specific_category


# Get details of individual asset details
def get_specific_asset_details(asset_name,token): 
    try:
        all_asset_details = None
        # Investor assets
        url = "https://api-uat.evident.capital/asset/investor/list?page=1"
        payload = json.dumps({"name":f"{asset_name.strip()}"})

        headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }

        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        all_asset_details = data['data'][0]
        # print(data)
        visibility = all_asset_details['visibility'][0]+all_asset_details['visibility'][1:].lower()
        # print(visibility)
        retirementEligible = 'Not Available'
        if all_asset_details['retirementEligible'] == False:
            retirementEligible = 'Not Available for this asset'
        else:
            retirementEligible = 'Asset is elgible'
        asset_url = all_asset_details['shortUrl']
        investment_details = ''
        if all_asset_details['investmentMode']=='Commitment':
            commitmentDetails = all_asset_details['commitmentDetails'][0]        
            commitmentStatus = commitmentDetails['status'].replace("_"," ") 
            startDate = commitmentDetails['startAt'].split("T")[0] if commitmentDetails['startAt'] is not None or commitmentDetails['startAt'] !='' else ''
            endDate = commitmentDetails['endAt'].split("T")[0] if commitmentDetails['endAt'] is not None or commitmentDetails['endAt'] !='' else ''
            investment_details = f"""Commitment Status - {commitmentStatus}\n
                                    Target Amount - {str(commitmentDetails['targetAmount'])}\n
                                    Minimum Investment Amount - {str(commitmentDetails['minimumAmount'])}\n
                                    Maximum Investment Amounr - {str(commitmentDetails['maximumAmount'])}\n
                                    Raised Amount - {str(commitmentDetails['raisedAmount'])}\n
                                    Start On - {startDate}\n
                                    End On - {endDate}
                                    """
            
        elif all_asset_details['investmentMode']=='Trading':
            tardeDetails = all_asset_details['investmentDetails']
            investment_details = f"""Open Offers - {tardeDetails['openOffers']}\nNumber of Investors - {tardeDetails['numberOfInvestors']}\nTotal invested amount - {tardeDetails['totalInvested']}\n"""
            
        keyHighlights = ""
        knum = 1
        for kh in all_asset_details['assetKeyHighlights']:
            keyHighlights = keyHighlights+str(knum)+'.'+kh['text']+'\n'
            knum+=1
        
        url = "https://api-uat.evident.capital/event/get-events-by-asset"
        payload = json.dumps({
        "assetId": data['data'][0]['id']
        })
        headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }

        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        data = data['data']
        # print(data)
        event_details = 'No ongoing events.'
        if data !=[]:
            evnNum = 1
            for evn in data:
                event_details = event_details+f"""{evnNum}. Event Title - {evn['title']}\nContent - {evn['content']}\nLink to Join Event - {evn['zoomLink']}\nStart Date - {evn['startDate']}\nEnd Date - {evn['endDate']}"""
        
        rateOfReturn = all_asset_details['rateOfReturn'] if all_asset_details['rateOfReturn'] is not None else 'Unavailable'
        exitStrategy = all_asset_details['exitStrategy'] if all_asset_details['exitStrategy'] is not None else 'Unavailable'
        try:
            manager = all_asset_details['manager']['kyc']['firstName'][0]+all_asset_details['manager']['kyc']['firstName'][1:].lower()+' '+all_asset_details['manager']['kyc']['lastName'][0]+all_asset_details['manager']['kyc']['lastName'][1:].lower()
        except:
            manager = 'Not Available'
        try:
            company = all_asset_details['manager']['company']['companyName']
        except:
            company = "Not Available"
        impacts = []
        impact_details = all_asset_details['impacts']
        for imp in impact_details:
            impacts.append(imp['name'])
        impacts = ", ".join(impacts)
        status = all_asset_details['status'][0].upper()+all_asset_details['status'][1:].lower()
        asset_info = f"""Asset Name - {all_asset_details['name']}
                      Asset Description - {all_asset_details['description']}
                      Asset Location - {all_asset_details['location']}
                      Asset Currency - {all_asset_details['currency']}
                      Asset Status - {status}
                      Visibility - {visibility}
                      Structuring - {all_asset_details['structuring']}                      
                      Asset vertical - {all_asset_details['assetVertical']}
                      Updates - Apologies, currently I am unable to provide you updates for this asset.
                      Retirement Elgibility - {retirementEligible}
                      Investment Mode - {all_asset_details['investmentMode']}                      
                      IRR(Internal Rate of Return/Rate of Return) - {rateOfReturn}
                      Impacts - {impacts}
                      Asset Manager - {manager}
                      Comapny Name - {company}
                      Investment Details - {investment_details}
                      Exit Strategy - {exitStrategy}
                      Key Highlights - {keyHighlights}                      
                      Events - {event_details}
                      """
        return asset_info,asset_url
    except Exception as e:
        logger.error(f"failed to get asset details - {str(e)}")
        return "No information found","Not available"

# Generate response based on provided asset specific detail
def get_asset_based_response(assets_identified,question,token):
    final_response = ''
    try:
        for ass in assets_identified:
            data,asset_url = get_specific_asset_details(ass,token)
            note = f"""Response Guidelines:
                    If an answer is fully available: Provide a clear, concise response with proper structure and formatting.
                    If some information is unavailable but the rest is available: Mention that the specific missing information is unavailable. If needed, suggest contacting support:
                    "Certain details are unavailable for this asset, but our support team would be happy to assist you. Please reach out to support@evident.capital with your query."
                    If no relevant information is available: Respond with:
                    "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at support@evident.capital with the details of your query, and they’ll assist you promptly."
                    Ask user to visit for more details - "{asset_url}" 
                    Note: The response should be clear, concise, and user-friendly, adhering to these guidelines. Encourage to ask more queries."""
            prompt = f"""Below is the asset details you have from Evident. Refer them carefully to generate answer. Check what kind of details user is asking about.
                To get proper trade values, add all results of that perticular assets. Do not provide paramters like id, and also create proper response it **SHOULD NOT** be in key value format.
                PROVIDE ALL INFORMATION TO USER, DO NOT SKIP ANY INFORMATION. IN CASE IF USER IS ASKING ABOUT ANY SPECIFIC DETAIL THEN PROVIDE ONLY THAT SPECIFIC DETAIL.
                NOTE - {note}
                Asset Details: - {data}
                RESPONSE GUIDELINES: STRICTLY FOLLOW THIS GUIDELINE WHILE PROVIDING RESPONSE. FOLLOW HTML FORMATTING AS SHOWN IN TEMPLATE ONLY.
                **DO NOT APPLY BULLETS, OR NUMBERING.**
                **Ensure line breaks are ONLY applied between different attributes, NOT within values.**
                **DO NOT APPLY LINE BREAKS BETWEEN ATTRIBUTE AND VALUE. FOLLOW :- "Attribute:Value" FORMAT**
                **STRUCTURE TEMPLATE TO CREATE ANSWER: STRICTLY FOLLOW THIS TEMPLATE TO ARRANGE AASSET DETAILS, IF ANY DETAILS IS UNAVAILABLE SKIP THAT TITLE IN CASE OF "Investment Details" AND "Events": **
                **"Events:","Investment Details:" AND "Key Highlights:" HAVE SUB POINTS. MAKE SURE MAIN POINTS AND SUB POINTS ARE IN PROPER DIFFERENTIATE MANNER. DO NOT TREAT MAIN POINTS AS SUBPOINTS WHILE APPLYING ANY KIND OF LISTING OR BULLETING.**
                **IF USER IS ASKING ABOUT ANY SPECIFIC DETAILS LIKE "MANAGER NAME", "EVENTS", "IRR", OR ANY OTHER KEY DETAILS PRESENT IN STRUCTURE. THEN PROVIDE ONLY THAT SPECIFIC INFORMATION. DO NOT PROVIDE ALL INFORMATION.
                **IF USER IS ASKING ABOUT INVESTMENT, COMMITMENT PROCESS OR STEPS IN ASSET THEN RETURN ONLY 'Apologies, currently I am not able to assit you with step by step details but You can start investment by clicking on "Invest" tab.'
                **COMPANY DOCUMENT IS AVAILABLE: Go to 'Company Document' -> 'NDA' pop-up will appear -> Click on 'I have read and agree to the terms of this NDA.' -> Click on 'Sign'**
                **TO DOWNLOAD COMPANY DOCUMENT: Go to 'Company Document' -> 'NDA' pop-up will appear -> Click on 'I have read and agree to the terms of this NDA.' -> Click on 'Sign' -> Click on 'Download all'
                **ASSET "TYPE" IS EQUAL TO ASSET "VERTICAL" AND ONLY "Target Amount" IS EQUAL TO "Allocated Amount"**
                **MAKE SURE YOU DO NOT SHOW ANY MAIN POINT AS SUB POINT OF ANYOTHER MAIN POINT.**
                **DO NOT WRITE ANY VALUE AS "None", INSTEAD KEEP IT AS "Unavailable"**
                **MAKE SURE IF SPECIFIC DETAILS ARE ASKED THEN SHARE ONLY AND ONLY SPECIFIC DETAILS**
                E.g.
                Asset Name - Abc
                Asset Description - this is asset's description
                Asset Location in Country - IND
                Asset Status - Completed
                Asset Visibility - Public
                Retirement Elgibility - Yes
                Investment Mode - Trade
                Structuring - Note
                Asset vertical/Type - Venture
                Asset Manager - Thomas
                Comapny Name - Evident LLP
                IRR(Internal Rate of Return/Rate of Return) - 10%
                Exit Strategy - Not available
                Impacts: Social, Planet saving
                Investment Details:
                        Open Offers - 2
                        Number of Investors - 10
                        Invested amount - 50000
                        Commitment Status - Completed
                        Target Amount/Allocated Amount - 5000
                        Minimum Investment Amount - 10
                        Maximum Investment Amount - 500
                        Raised Amount - 2000
                        Start On - 10-2-2025
                        End On - 10-3-2025                
                Key Highlights:
                        asset works good
                        progress happend with 10%                
                Events:
                        Event Title - Onboarding Introduction
                        Content - hello how are you
                        Link to Join Event - https://samplelink.com
                        Start Date - 03-03-2025
                        End Date - 05-03-2025
                """
            response = get_gemini_response(question,prompt)      
            final_response = final_response + '\n'+ response  
        logger.info(f"asset based response - {final_response}")
    except Exception as e:
        logger.error(f"failed while handling asset based question - {str(e)}")
    return final_response


# Question handling flow - IP Count:9, OP Count:3
def handle_questions(token, last_asset, last_ques_cat, user_name, user_role, current_question, onboarding_step):     
    logger.info(f"\nlast_asset - {last_asset}\nuser_role - {user_role}\nlast_ques_cat - {last_ques_cat}")
    asset_found = ''
    response = ''
    current_asset = last_asset
    isRelated = False
    isAssetRelated = False   
    isPersonalAsset = False

    asset_names  = get_asset_list()
    asset_names = list(asset_names)
    asset_names = ", ".join(asset_names)+", DND small cap funds, Uma Landry"
    prompt = f"""TO RETURN NAME OF ASSET:  
                Last Question Category - `{last_ques_cat}`  

                ### **Step 1: If Explicit Asset Name is Found, Return Asset Name**
                - Normalize asset names for matching by **removing spaces, dashes, and capitalization** before comparison.  
                - If the question contains an **exact match** or **a close match** (considering typos/misspellings), return that asset name immediately.  
                - **If a new asset is matched, update the active asset before returning the result.**  
                - **STRICTLY DO NOT return `{last_asset}` if a new asset is found.**  
                - Treat **spaces (" "), dashes ("-"), and underscores ("_") as equivalent** when matching asset names.  
                - **Ignore case sensitivity** when matching.  
                - **"&" and "and" should be treated as equivalent.**  
                - **Once an asset is matched, STOP further processing.**  

                #### **Asset Name Matching Priority:**  
                - If an exact asset name is found in `{asset_names}`, return it immediately.  
                - If a close match (with minor typos/misspellings) is found, return the closest matching asset.  
                - Treat **"&" and "and"** as equivalent when matching asset names.  
                - **Normalize asset names before comparison** (remove spaces, dashes, underscores, and convert to lowercase).  
                - If multiple assets match, separate them with `","`.  

                #### **Example Normalization:**
                | User Input  | Matched Asset |
                |-------------|--------------|
                | OpenAI      | OpenAI       |
                | Open AI     | OpenAI       |
                | Open-AI     | OpenAI       |
                | open ai     | OpenAI       |
                | openai      | OpenAI       |
                | open_ai     | OpenAI       |

                - If an asset is found, **STOP and return the name immediately**.  
                - If no match is found, continue to Step 2. 

                ### **Step 2: If Last Question Category is "Owned Assets", Return "1"**
                - If `{last_ques_cat} == "Owned Assets"` and question is about user-owned assets, holdings, trades, and commitments, **IMMEDIATELY RETURN `"1"`**.  
                - **DO NOT check for `{last_asset}` here.**  
                - Owned Asset Data (ONLY THIS DATA IS AVAILABLE):
                    - Trade Details: Trade Asset, Price, Total Units, Available Units, Trade Units, Trade Status, Number of Clients, Asset Maker
                    - Commitment Details: Asset Name, Commitment Amount, Allotted Units, Commitment Status  
                - If question is unrelated to these topics, proceed to Step 3.  

                ### **Step 3: If Last Question Category is "Personal Assets" and a Relevant Topic is Found, Return `{last_asset}`**
                - If `{last_ques_cat} == "Personal Assets"`, **ONLY return `{last_asset}` if Step 1 DID NOT FIND A NEW ASSET**.  
                - **If Step 1 found a new asset, `{last_asset}` is ignored.**  

                **Relevant Topics (For Personal Assets Only)**:  
                    - Name (e.g., Title, Label, Designation)  
                    - Description (e.g., Details, Summary, Overview, Information)  
                    - Location (e.g., Country, Region, Place, Address, Jurisdiction)  
                    - Currency (e.g., Money, Denomination, Trading Currency, Financial Unit)  
                    - Status (e.g., Condition, Current State, Standing, Availability)  
                    - Structuring (e.g., Organization, Framework, Setup, Type)  
                    - Vertical/Type (e.g., Category, Industry, Asset Class, Classification)  
                    - Updates (e.g., Modifications, Changes, Revisions, Latest Information)  
                    - Retirement Eligibility (e.g., Maturity, Expiry, Withdraw Criteria)  
                    - Investment Mode (e.g., Trading Method, Funding Type, Capital Deployment)  
                    - IRR (Internal Rate of Return/Rate of Return) (e.g., ROI, Yield, Profitability, Earnings Rate)  
                    - Impacts (e.g., Effect, Influence, ESG Factors, Sustainability, Social Responsibility)  
                    - Manager (e.g., Asset Manager, Fund Manager, Portfolio Manager, Administrator)  
                    - Company (e.g., Organization, Entity, Business, Firm, Issuer)  
                    - Investment Details (e.g., Funding Information, Capital Info, Portfolio Details, Including Asset-specific: Trades and Commitments)  
                    - Commitment Details (e.g., Target Amount, Minimum Investment Amount, Maximum Investment Amount, Raised Amount)  
                    - Trade Details (e.g., Open Offers, Number of Investors, Total Invested Amount)  
                    - Open Offers (e.g., Available Deals, Active Investments, Ongoing Offers)  
                    - Number of Investors (e.g., Total Investors, Investor Count, Stakeholders)  
                    - Total Invested Amount (e.g., Capital Deployed, Funds Raised, Total Funding)  
                    - Exit Strategy (e.g., Liquidity Plan, Withdrawal Plan, Disinvestment Plan)  
                    - Key Highlights (e.g., Important Points, Notable Features, Core Insights)  
                    - Events (e.g., Occurrences, Announcements, Happenings, Ongoing Activities)  

                ### **Step 4: If question is related or in context of previous category, Return "2"**
                - If the current question is related to the previous question category, STRICTLY RETURN `2`.  

                ### **Step 5: If question does not belong to any of the above mentioned steps, Return "0"**
                - If the question does not match any of the above steps, RETURN `"0"`.  

                **STRICTLY REPLY WITH EITHER 0, 1, 2, OR THE EXACT ASSET NAME. NO ADDITIONAL TEXT IS ALLOWED.**"""

    # prompt = f"""TO RETURN NAME OF ASSET:  
    #             Last Question Category - `{last_ques_cat}`  

    #             ### **Step 1: If Explicit Asset Name is Found, Return Asset Name**
    #             - If the question contains an **exact match** or **a close match** (with typos/misspellings), RETURN that asset name.  
    #                 Asset Name Matching Priority:   
    #                     - If you  identify an exact asset name  from the list, return that exact value.  
    #                     - If you find a  similar  asset name that the user might be referring to (considering typos, misspellings, or approximate context), return the closest matching asset name from the list.  
    #                     - Treat  "&" and "and"  as equivalent when matching asset names.  
    #                     -  If the user has not explicitly mentioned an asset name but is referring to a previously mentioned one, return `{last_asset}`.   
    #                     -  If the question explicitly asks about an asset (like "Who is the manager of XYZ?"), RETURN only the ASSET NAME and do not classify this as a general investment query.   
    #                 Asset Names - {asset_names}
    #             - If multiple assets match, separate them with `","`.                    
    #             - If asset name is found strictly return asset name from "Asset Names"  
    #             - If no match is found, continue to Step 3. 

    #             ### **Step 2: If Last Question Category is "Owned Assets", Return "1"**
    #             - If `{last_ques_cat} == "Owned Assets"` and question is about user-owned assets, holdings, trades, and commitments, **IMMEDIATELY RETURN `"1"`**—DO NOT check for `last_asset`.  
    #             - This ensures that **user-owned assets, holdings, trades, and commitments always return `"1"`**.  
    #             - Owned Assets have ONLY following data: If question is related to following data while Last Question Category is "Owned Assets" : Return '1'.
    #                 Owned Asset Data(**ONLY THIS DATA IS AVAILABLE**): IF QUESTION IS ABOUT ANYTHING ELSE THAN BELOW MENTIONED TOPIC THEN REFER TO OTHER STEPS - 
    #                     Trade Details:- Trade Asset, Price, Total Units, Available Units, Trade Units, Trade Status, Number of Clients, Asset Maker
    #                     Commitment Details:- Asset Name, Commitment Amount, Allotted Units, Commitment Status
                
    #             ### **Step 3: If Last Question Category is "Personal Assets" and a Relevant Topic is Found, Return `{last_asset}`**
    #             - If `{last_ques_cat} == "Personal Assets"` **AND** the question is related to **Relevant Topics** below, RETURN `{last_asset}`.  

    #             ### **Relevant Topics (For Personal Assets Only)**
    #             - Name (e.g., Title, Label, Designation)  
    #             - Description (e.g., Details, Summary, Overview, Information)  
    #             - Location (e.g., Country, Region, Place, Address, Jurisdiction)  
    #             - Currency (e.g., Money, Denomination, Trading Currency, Financial Unit)  
    #             - Status (e.g., Condition, Current State, Standing, Availability)  
    #             - Structuring (e.g., Organization, Framework, Setup, Type)  
    #             - Vertical/Type (e.g., Category, Industry, Asset Class, Classification)  
    #             - Updates (e.g., Modifications, Changes, Revisions, Latest Information)  
    #             - Retirement Eligibility (e.g., Maturity, Expiry, Withdraw Criteria)  
    #             - Investment Mode (e.g., Trading Method, Funding Type, Capital Deployment)  
    #             - IRR (Internal Rate of Return/Rate of Return) (e.g., ROI, Yield, Profitability, Earnings Rate)  
    #             - Impacts (e.g., Effect, Influence, ESG Factors, Sustainability, Social Responsibility)  
    #             - Manager (e.g., Asset Manager, Fund Manager, Portfolio Manager, Administrator)  
    #             - Company (e.g., Organization, Entity, Business, Firm, Issuer)  
    #             - Investment Details (e.g., Funding Information, Capital Info, Portfolio Details, Including Asset-specific: Trades and Commitments)  
    #             - Commitment Details (e.g., Target Amount, Minimum Investment Amount, Maximum Investment Amount, Raised Amount)  
    #             - Trade Details (e.g., Open Offers, Number of Investors, Total Invested Amount)  
    #             - Open Offers (e.g., Available Deals, Active Investments, Ongoing Offers)  
    #             - Number of Investors (e.g., Total Investors, Investor Count, Stakeholders)  
    #             - Total Invested Amount (e.g., Capital Deployed, Funds Raised, Total Funding)  
    #             - Exit Strategy (e.g., Liquidity Plan, Withdrawal Plan, Disinvestment Plan)  
    #             - Key Highlights (e.g., Important Points, Notable Features, Core Insights)  
    #             - Events (e.g., Occurrences, Announcements, Happenings, Ongoing Activities)  

    #             ### **Step 4: If question is related or in context of previous category, Return "2"**
    #             - If the current question is related to the previous question category, STRICTLY RETURN `2`.                  
                
    #             ### **Step 5: If question does not belong to any of the above mentioned steps i.e. from Step 1 to Step 4, Return "0"**
    #             - If the question does not match any to any of the above steps, RETURN `"0"`.

    #             STRICTLY REPLY IN THE ABOVE FORMAT. DO NOT ADD ANYTHING ELSE IN YOUR RESPONSE. **RESPONSE SHOULD EITHER 0,1,2, OR NAME OF ASSET NOTHING ELSE IS ACCEPTABLE AS RESPONSE.**"""
    asset_identified_flag = get_gemini_response(current_question,prompt)
    logger.info(f'asset_identified_flag - {asset_identified_flag}')
    promp_cat = []
    print(asset_names)
    try:
        if int(asset_identified_flag)==1:
            """Owned asset"""
            isPersonalAsset = True
            isAssetRelated = True
            promp_cat.append('Personal_Assets')
        elif int(asset_identified_flag)==0:
            """Non asset related"""
            promp_cat = get_prompt_category(current_question,user_role,last_asset,last_ques_cat)
            promp_cat = promp_cat.split(",")
            promp_cat = [p.strip() for p in promp_cat]  
            print("promp_cat - ",promp_cat)
            if 'Personal_Assets' in promp_cat:
                prompt = f"""FOLLOW BELOW INSTRUCTIONS STRICTLY:  
                Last Question Category - `{last_ques_cat}`  

                **If Explicit Asset Name is Found, Return Asset Name**
                - If the question contains an **exact match** or **a close match** (with typos/misspellings), RETURN that asset name.  
                - If multiple assets match, separate them with `","`.  
                - If name of asset is found strictly return asset name.                
                Asset Name Matching Priority:   
                    - If you  identify an exact asset name  from the list, return that exact value.  
                    - If you find a  similar  asset name that the user might be referring to (considering typos, misspellings, or approximate context), return the closest matching asset name from the list.  
                    - Treat  "&" and "and"  as equivalent when matching asset names.  
                    - If the question explicitly asks about an asset (like "Who is the manager of XYZ?"), RETURN only the ASSET NAME and do not classify this as a general investment query.   
                Asset Names - {asset_names}
                -  If the user has not explicitly mentioned an asset name but is referring to a previously mentioned one, return `{last_asset}`.   
                - If no match is found, return 0. 
                ### **Relevant Topics TO ASSETS**
                - Name (e.g., Title, Label, Designation)  
                - Description (e.g., Details, Summary, Overview, Information)  
                - Location (e.g., Country, Region, Place, Address, Jurisdiction)  
                - Currency (e.g., Money, Denomination, Trading Currency, Financial Unit)  
                - Status (e.g., Condition, Current State, Standing, Availability)  
                - Structuring (e.g., Organization, Framework, Setup, Type)  
                - Vertical/Type (e.g., Category, Industry, Asset Class, Classification)  
                - Updates (e.g., Modifications, Changes, Revisions, Latest Information)  
                - Retirement Eligibility (e.g., Maturity, Expiry, Withdraw Criteria)  
                - Investment Mode (e.g., Trading Method, Funding Type, Capital Deployment)  
                - IRR (Internal Rate of Return/Rate of Return) (e.g., ROI, Yield, Profitability, Earnings Rate)  
                - Impacts (e.g., Effect, Influence, ESG Factors, Sustainability, Social Responsibility)  
                - Manager (e.g., Asset Manager, Fund Manager, Portfolio Manager, Administrator)  
                - Company (e.g., Organization, Entity, Business, Firm, Issuer)  
                - Investment Details (e.g., Funding Information, Capital Info, Portfolio Details, Including Asset-specific: Trades and Commitments)  
                - Commitment Details (e.g., Target Amount, Minimum Investment Amount, Maximum Investment Amount, Raised Amount)  
                - Trade Details (e.g., Open Offers, Number of Investors, Total Invested Amount)  
                - Open Offers (e.g., Available Deals, Active Investments, Ongoing Offers)  
                - Number of Investors (e.g., Total Investors, Investor Count, Stakeholders)  
                - Total Invested Amount (e.g., Capital Deployed, Funds Raised, Total Funding)  
                - Exit Strategy (e.g., Liquidity Plan, Withdrawal Plan, Disinvestment Plan)  
                - Key Highlights (e.g., Important Points, Notable Features, Core Insights)  
                - Events (e.g., Occurrences, Announcements, Happenings, Ongoing Activities)  

                REFER BELOW EXAMPLES TO GENERATE RESPONSE:
                Q: Tell me about openai
                A: OpenAI - Co-Investment
                Q: Provide me details and overview about spacex
                A: SpaceX - Co-Investment
                Q: Who is manager for openai
                A: OpenAI - Co-Investment
                Q: what is IRR for this?
                A: {last_asset}
                """
                asset_identified_flag = get_gemini_response(prompt,current_question)
                logger.info(f"asset_identified_flag 0 - {asset_identified_flag}")
                current_asset = asset_identified_flag
        elif int(asset_identified_flag)==2:
            temp_last_ques_cat = last_ques_cat.split(",")
            promp_cat = get_prompt_category(current_question,user_role,last_asset,last_ques_cat)
            promp_cat = promp_cat.split(",")
            promp_cat = [p.strip() for p in promp_cat]  
            temp_last_ques_cat = promp_cat + temp_last_ques_cat
            for cat in temp_last_ques_cat:
                if 'onboarding' in cat:
                    promp_cat.append(cat)
                    break
    except:
        """Name of asset"""   
        promp_cat=['Personal Assets']
        names = asset_names.split(", ")
        for n in names:
            if asset_identified_flag in n:
                isAssetRelated = True
                current_asset = asset_identified_flag
                break
        else:
            current_asset = asset_identified_flag
        logger.info(f"asset_identified_flag except - {asset_identified_flag}")

    # If question is just a greeting nothing else is asked in that question
    if 'Greetings' in promp_cat[0] and len(promp_cat)==1:
        prompt = f"""User name is - {user_name}, reply to user in polite and positive way. Encourage for further communication. if user name is not present then skip using user's name. 'Please let me know if you have any other questions...' or 'Is there anything else...' As it can be user's 1st message. DO NOT FRAME ANSWER IN THIS WAY, INSTEAD ASK HOW YOU CAN HELP USER."""
        response = get_gemini_response(current_question,prompt)
        logger.info(f"response from greetings - {response}")
        return response,'','Greetings'
    # Remove greetings category from prompt categories
    else:
        promp_cat = [p.strip() for p in promp_cat if 'Greetings' not in p.strip()]
    logger.info(f"Prompt categories - {promp_cat}")
    response,asset_found,specific_category = category_based_question(current_question,promp_cat,token,onboarding_step,isRelated,isAssetRelated,last_ques_cat,current_asset,isPersonalAsset)
    # logger.info(f"final response from handle_questions - {response}")
    specific_category = ",".join(specific_category)
    # print("specific_category= ",specific_category)
    return response,asset_found,specific_category


# @csrf_exempt
def login(request):
    # print("in login")
    url = "https://api-uat.evident.capital/user/login"
    payload = json.dumps({
    # "email": "shweta+indinvuat03@evident.capital",
    # "password": "Evident@2024",
    "email": "sai+0303ind@gmail.com",
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
    token = data['token']
    return JsonResponse({"token":token},status=200)


def format_response(response):
    # Normalize list formatting
    response = re.sub(r'\n\s*-\s*', '\n- ', response)  # Fix unordered lists
    response = re.sub(r'\n\s*\*\s*', '\n- ', response)  # Convert * to -

    # Ensure proper numbered list spacing
    response = re.sub(r'(\d+)\.\s*', r'\n\1. ', response)  

    # Convert italic formatting (_text_ or *text*) to bold (**text**)
    response = re.sub(r'(?<!\*)\*(\S.*?)\*(?!\*)', r'**\1**', response)  
    response = re.sub(r'_(\S.*?)_', r'**\1**', response)  

    # Convert new lines for Markdown-friendly format
    response = response.replace("\n", "  \n")  
    # Fix unwanted line breaks between labels and values (Price - X, Trade Units - Y)
    response = re.sub(r'(\b(Price|Trade Units|Total Units|Available Units|Commitment Amount|Alloted Units|Raised Amount|Number of Investors|Open Offers|Total Invested Amount|IRR)\s*-\s*)\n', r'\1 ', response)
    response = re.sub(r'(\b(Price|Trade Units|Total Units|Available Units|Commitment Amount|Alloted Units|Raised Amount|Number of Investors|Open Offers|Total Invested Amount|IRR)\s*:\s*)\n', r'\1 ', response)
    
    # Remove **unstructured** numbering (standalone numbers at the start of a line)
    # response = re.sub(r'^\d+\.\s*', '', response, flags=re.MULTILINE)
    response = re.sub(r'^-\s*', '', response, flags=re.MULTILINE)

    # Convert Markdown to HTML
    # html_content = markdown.markdown(response)
    # html_content = html_content.replace("*","").replace("<em>","").replace("</em>","").replace("","").replace("","")
    
    return response

# Main flow
@csrf_exempt
def evidAI_chat(request):
    try:
        if request.method == 'POST':
            
            token = None
            # Extract the Bearer token from the Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({"message":"missing header, please pass authentication token","data":{"response":"No authentication token present"},"status":False},status=400)

            # Get the token and validate it
            token = auth_header.split(' ')[1]
            token_valid,user_id,user_name,user_role,onboarding_step = token_validation(token)

            if token_valid is None:
                logger.error(f"Invalid Token, Token: {token}")            
                return JsonResponse({"message":"Invalid user, please login again","data":{"response":"Failed to validate token for user, please check token"},"status":False},status=400)
            
            data = json.loads(request.body)
            current_question = data.get('question')
            chat_session_id = int(data.get('chat_session_id'))

            # chat session validation
            chat_session_validation = validate_chat_session(chat_session_id)
            if chat_session_validation is None:
                logger.error(f'Invalid chat session, kindly create new chat session for user ID - {user_id}')
                return JsonResponse({"message":"Unexpected error occured","data":{
                "response":"Invalid chat session, kindly create new chat session"},"status":False},status=200)
            
            previous_questions, last_asset, last_ques_cat = get_conv_details(chat_session_id)

            # Update title
            if len(previous_questions)==1:
                update_chat_title(current_question,chat_session_id)
                
            response, current_asset, current_ques_cat = handle_questions(token, last_asset, last_ques_cat, user_name, user_role, current_question, onboarding_step)
            response = response.replace("\n", "  \n")  
            add_to_conversations(user_id, chat_session_id, current_question, response, current_asset, current_ques_cat)      
            
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

            prompt_table = models.BasicPrompts.objects.get(prompt_category=category)
            prompt_table.prompt = value
            prompt_table.save()

            prompt_table = models.BasicPrompts.objects.get(prompt_category=category)
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
            # Convert to ISO 8601 format
            iso_format_datetime = current_datetime.isoformat()
            new_cat = models.BasicPrompts.objects.create(
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


def add_prompt_to_UAT():
    data = models.BasicPrompts.objects.exclude(prompt_category='Existing Assets').all().values()
    for d in data:
        if d['prompt_category'] in ['Forget Password','Corp Investor Onboarding','Onboarding Investor']:
            continue
        # print(d['prompt_category'])
        value = d['prompt']
        category = d['prompt_category']
        asset_name = d['asset_name'][0] if d['asset_name'] is not None else ""
        asset_sub_cat = d['asset_sub_cat'][0] if d['asset_sub_cat'] is not None else ""
        url = "https://chatbot-api.evident.capital/add_prompt_values"

        payload = json.dumps({"value":value,"category":category,"asset_name":asset_name,"asset_sub_cat":asset_sub_cat})
        headers = {}
        # print(payload)
        response = requests.request("POST", url, headers=headers, data=payload)

        # print(response.content)
