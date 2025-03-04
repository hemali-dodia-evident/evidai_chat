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
        response = "Sorry! I am not able to find answer for your question. \nRequest you to coordinate with our support team on - hello@evident.capital.\nThank You."
        return response


# Identify prompt category based on current and previous questions
def get_prompt_category(current_question,user_role):
    logger.info("Finding prompt from get_prompt_category")
    prompt = f"""Based on user's question identify the category of a question from below mentioned categories. STRICTLY PROVIDE ONLY NAME OF CATEGORIES NOTHING ELSE, IF NO CATEGORY MATCHES THEN RETURN "FAILED".
                 Note - While answering do not add any other information or words. Just reply as per specified way. ONLY PROVIDE ONLY NAME OF CATEGORIES. 
                 USER's QUESTION - {current_question}
                 USER's ROLE - {user_role}
                 Greetings: Contains generic formal or friendly greetings like hi, hello, how are you, who are you, etc. It DOES NOT contain any other query related to below catrgories mentioned below.
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
                    that asset, commitments. Here user asks about different things on asset. 
                    These are user specific assets. When user wants to know about his/her asset details.
                 Forget_Password: Contains step by step process to change or update password.
                 Assets_Creation: Detailed process only to create assets. 
                 Asset_Managers:This category contains information about EVIDENT's due diligence process for asset managers, the structuring and tokenization of assets, and the various fundraising methods available on the platform, emphasizing efficiency, transparency, and investor protection.
                 Onboarding_Distributor:Detailed process for distributor onboarding process.
                 Onboarding_Issuer:Detailed process for issuer onboarding process.
                 Corp_Investor_Onboarding:Detailed process for Corp investor onboarding process.
                 Onboarding_Investor:Detailed process for investor onboarding process.
                 Licensing_Custody:This category contains information about EVIDENT's regulatory compliance, including multiple licenses such as TCSP and SFC, investor protection measures, and secure handling of user funds in segregated accounts using blockchain technology.
                 Account_Opening_Funding:This category contains information about EVIDENT's streamlined and digitalized account opening process, including automated KYC and AML checks for security and regulatory compliance, and the convenient and secure procedure for depositing funds via bank transfer.
                 Security:This category contains information about EVIDENT's hybrid approach to cyber security, combining centralized and decentralized elements, the use of advanced security protocols and Algorand blockchain, compliance with financial regulations, and additional features like transaction rollbacks and IP whitelisting to protect against potential threats.
                 Product_Technology:EVIDENT is a platform for tokenizing and investing in alternative assets using blockchain technology, with features like Commitment Campaigns to raise capital, buy and sell tokenized assets, and handle asset liquidation securely. It ensures regulatory compliance and investor protection through a hybrid setup, accepting multiple currencies with spot rate exchange for non-USD funds.
                 Platform_Differentiation: EVIDENT is a fully integrated, SFC-licensed platform in Hong Kong for alternative assets, using tokenization for efficient and cost-effective investment and management of Real-World Assets.
                 Asset_Tokenization: EVIDENT tokenizes a wide range of assets, using SPVs for tangible assets and digitalization for intangible ones, ensuring regulatory compliance through "Digital Securities."
                 Digital_Transformation: EVIDENT bridges conventional financial markets and digital technologies using web3, enhancing accessibility, transparency, and efficiency with a hybrid centralized-decentralized approach.
                 Self_Custody:This category contains information about EVIDENT's support for users to self-custody their digital units in separate wallets, while ensuring compatibility with external systems, regulatory compliance, and investor protection.
                 SPV_Plan:Detailed step by step process to create SPV plan
                 SPV_Strurcture:Detailed step by step process to create SPV structure
                 About_Company:All the details about evident platfor, company and founders, services.
                 Legal_And_Regulatory:This prompt provides a comprehensive rationale for why Evident does not require a VATP license or Type 4/7/9 licenses in Hong Kong. It emphasizes the legal and regulatory positioning of Evident's hybrid model, which combines blockchain technology with centralized record-keeping, ensuring compliance with existing securities laws and the enforceability of token holders' rights.
                 Custody:This prompt outlines where customer funds are held, how they are managed and reflected on the platform, the custody practices of EVIDENT regarding underlying shares/tokens, and the transferability and tradeability of tokens outside the platform, with conditions for off-platform asset holding.
                 Structuring:This prompt explains how legal titles and share certificates are handled within EVIDENT's SPV structure, emphasizing the streamlined process for transferring legal titles at the SPV level rather than with each investor transaction.
                 Commitment_Campaign:This prompt outlines the process and mechanics of a Commitment Campaign on the EVIDENT platform, detailing how investor funds are managed during the campaign, including the handling of commitments, escrow, and the issuance of tokens.
                 buy_and_sell_tokenized_assets:This prompt describes how investors can buy and sell tokenized assets on the EVIDENT platform, covering the process of committing to investments and trading tokens within the platform's regulatory framework.
                 asset_failure_handling:This prompt explains EVIDENT's procedures for handling situations where the acquisition of target assets fails or when an asset needs to be liquidated, including the return of funds to investors and the involvement of asset managers.
                 customer_service_dispute:This prompt details how EVIDENT handles customer service and dispute resolution, highlighting the available support channels and the process for resolving disputes, including escalation if needed.
                 NOTE - IF MORE THAN ONE CATEGORY MATCHES THEN RETURN THEIR NAME WITH "," SEPERATED.
                 E.g. Qestion: What are the steps for investor onboarding?
                      Bot: Onboarding_Investor, Corp_Investor_Onboarding
                      Question: can you give me details about buying tokenized assets?
                      Bot: buy_and_sell_tokenized_assets
                      Question: Tell me about openai
                      Bot: Personal_Assets
                      Question: Hey i want some help
                      Bot: Greetings
                 """
    response = get_gemini_response(current_question,prompt)
    logger.info(f"prompt category - {response}")
    return response


# Authenticate from jwt token we are getting from UI
@csrf_exempt
def token_validation(token):    
    try:
        # Validate token 
        twoFA_url = "https://api-uat.evident.capital/user/two-factor-authentication"
        payload = json.dumps({
                "code": "123456",
                "ipAddress": "127.0.0.1"
                })
        headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
        response = requests.request("POST", twoFA_url, headers=headers, data=payload)
        data = response.json()
        # if data['code']=='2FA_VERIFIED':
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
        user_name = data['user']['kyc']['fullName'].split()[0]
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
            return None, None, None, None, None
        # else:
        #     return None, None, None, None, None
    except:
        return None, None, None, None, None


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
    Use proper formatting to enhance readability."""
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
    last_asset = ''
    last_ques_cat = ''
    if len(previous_questions)>1:
        last_asset = all_convo[0].is_asset
        last_ques_cat = all_convo[0].last_ques_cat    
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

    
# @csrf_exempt
# def delete_multiple_chat_session(request):
#     if request.method=="POST":
#         data = json.loads(request.body)
#         chat_session_id = data.get("chat_session_id")
#         deleted_sessions = {}
#         try:
#             for chats in chat_session_id:
#                 chat = models.ChatSession.objects.get(id=chats)
#                 chat.show = False
#                 chat.save()
#                 deleted_sessions['chat_session_id']=chats
#                 deleted_sessions['title']=chat.title
#         except Exception as e:
#             log_message(str(e))
#             return JsonResponse({"message":"Failed to delete Chat session","data":[],"status":False},status=200)
#         return JsonResponse({"message":"Chat session deleted successfully","data":deleted_sessions,"status":True},status=200)
#     else:
#         log_message('Invalid JSON format')
#         return JsonResponse({"message":"Invalid request type, POST method is expected","data":[],"status":False},status=200)


# @csrf_exempt
# def chat_page(request):
    if request.method == 'GET':
        # Render the HTML page for GET requests
        return render(request, 'evidentchatbot.html') 
    

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
                    Do not greet the user in your response. If you are unable to find answer then just say "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at hello@evident.capital with the details of your query, and they’ll assist you promptly."
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
    trades = data['trades']
    trade_details = None
    if trades == []:
        trade_details = "No trade available"
    else:
        trade_details = []
        for trd in trades:
            temp = {}
            temp['uniqueTradeId']=trd['uniqueTradeId']
            temp["price"]=trd["price"]
            temp["totalUnits"]=trd["totalUnits"]
            temp["availableUnits"]=trd["availableUnits"]
            temp["tradedUnits"]=trd['tradedUnits']
            temp['status']=trd['status']
            temp['createdAt']=trd['createdAt'].split("T")[0]
            temp['updatedAt']=trd['updatedAt'].split("T")[0]
            temp["numberOfClients"]=trd["numberOfClients"]
            temp["assetCurrency"]=trd["asset"]["currency"]
            temp['assetMaker']=trd['maker']
            temp = json.dumps(temp)
            trade_details.append(temp, indent=4)
        trade_details = ",".join(trade_details)

    commitments = data['commitments']
    commitment_details = None
    if commitments == []:
        commitment_details = "No commitments available"
    else:
        commitment_details = []
        for commit in commitments:
            temp = {}
            temp['commitmentDetails']=commit['commitmentDetails']
            temp['commitmentAmount']=commit['commitmentAmount']
            temp['allotedUnits']=commit['allotedUnits']
            temp['commitmentStatus']=commit['status']
            temp = json.dumps(temp, indent=4)
            commitment_details.append(temp)
        commitment_details = ",".join(commitment_details)
    my_assets = [trade_details,commitment_details]
    return my_assets


# Get list of all assets from DB
def get_asset_list():
    asset_names = models.Asset.objects.exclude(visibility='PRIVATE').values_list('name',flat=True)
    return asset_names


# Check category of question and then based on category generate response
# IP Count:10, OP Count:3
def category_based_question(current_question,previous_questions,promp_cat,token,user_id,onboarding_step,isRelated,isAssetRelated,last_asset,last_ques_cat):
    logger.info(f"In general cat based area data - {(current_question,previous_questions,promp_cat,token,user_id,onboarding_step,isRelated,isAssetRelated)}")
    try:
        question = current_question
        final_response = ""
        asset_found = ''
        promp_cat_new = ",".join(promp_cat)
        specific_category = promp_cat_new.replace("_",' ').split(',')
        logger.info(f"Categories identified by bot - {specific_category}")
        assets_identified = ""
        for promp_cat in specific_category:   
            logger.info(f"Getting answer for category - {promp_cat}")    
            if (promp_cat!='FAILED' and promp_cat !='Personal Assets'): #or (isRelated==True and (isAssetRelated==False and last_asset=='')):
                logger.info("General category based question")
                try:
                    categories = last_ques_cat.split(",")
                    categories.append(promp_cat)
                    data = models.BasicPrompts.objects.filter(prompt_category__in=categories)
                    prompt_data_list = []
                    for d in data:
                        prm = d.prompt
                        if 'Onboarding' in promp_cat:
                            prm = f"""{prm} \nUser\'s current onboarding status - {onboarding_step}
                                    If user's any step is not having stepStatus as 'COMPLETED' then ask user to Complete that step."""
                        prompt_data_list.append(prm)
                    logger.info(prompt_data_list)
                    prompt_data = f"""Customer is not providing you any information, all information is with you, DO NOT SAY TO CUSTOMER THAT THEY HAVE NOT PROVIDED INFORMATION,INSTEAD SAY YOU DONT HAVE INFORMATION CURRENTLY ON THIS. You are smart and intelligent chat-bot having good knowledge of finance sector considering this chat with user. 
                    Provide answer in a way that you are chatting with customer. Do not use any kind of emojis. Do not greet user while answering. Guide and help user to finish their steps and complete onboarding. Use below information to get answer -
                    {prompt_data_list}
                    NOTE - If you are not able to find answer then say "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at hello@evident.capital with the details of your query, and they’ll assist you promptly."
                    Keep tone positive and polite while answering user's query. Do NOT use any kind of formating like "*" just give proper line breaks using '\n'"""
                    response = get_gemini_response(question,prompt_data)
                    final_response = final_response + '\n' + response    
                except Exception as e:
                    logger.info(f"Failed to find general category related information in DB - {str(e)}")
                    prm = """For this topic currently we don't have any information. 
                    Provide answer in a way that "I’m sorry I couldn’t assist you right now. 
                    However, our support team would be delighted to help! Please don’t hesitate to email 
                    them at hello@evident.capital with the details of your query, and they’ll assist you promptly." 
                    this will cover the part of question for which information is not available"""
                    final_response = get_gemini_response(question,prm)
                asset_found = ''
            elif promp_cat=='FAILED':
                logger.info("Prompt Category is 'FAILED'")
                response = search_on_internet(question)
                asset_found = ''
                final_response = final_response + '\n' + response   
            elif 'Personal Assets' in promp_cat or (isRelated==True and isAssetRelated==True) or isAssetRelated==True:    
                logger.info("Prompt Category is Personal Asset") 
                personalAssets = False
                if isRelated==True and isAssetRelated==True:
                    # print(f"\n\nisRelated, isAssetRelated - {isRelated,isAssetRelated}")
                    assets_identified = [last_asset]
                else:
                    
                    all_assets_names = get_asset_list()
                    # print(f"\n\n{all_assets_names}\n\n")
                    prompt = f"""
                                Follow these instructions **exactly**:
                                - If the question is about assets owned, personal, or invested by the user, **return only `1`**.
                                - If the question asks about a **specific asset**, return **only the asset name** from the list below (if multiple, separate with commas `,`).
                                - If the question asks about **All assets in general**, **return only `2`**.
                                - **For all other questions, return only `0`**.
                                - **DO NOT add any extra words, explanations, or formatting**. Only return the specified response.

                                General Asset List:
                                {all_assets_names}

                                **STRICT EXAMPLES:**  
                                **Q:** "What is the commitment status of my assets?"  
                                **A:** `1`  
                                **Q:** "What is the minimum investment amount for Keith Haring?"  
                                **A:** `Keith Haring - Untitled`  
                                **Q:** "What are highlights of Mumbai?"  
                                **A:** `0`  
                                **Q:** "What is the minimum investment amount for OpenAI and Keith Haring?"  
                                **A:** `Keith Haring - Untitled,OpenAI - Co-Investment`  
                                **Q:** "Provide me list of all assets."  
                                **A:** `2`  

                                **DO NOT DEVIATE FROM THESE RULES. ONLY RESPOND AS SHOWN ABOVE.**  
                                """
                    asset_response = get_gemini_response(current_question,prompt)
                    logger.info(f"asset_response - {asset_response}")
                    try:
                        if int(asset_response.strip())==1:
                            assets_identified = users_assets(token)
                            personalAssets = True
                        elif int(asset_response.strip())==2:
                            assets_identified = all_assets_names[:3]
                        elif int(asset_response.strip())==0:
                            assets_identified = ''
                    except:
                        assets_identified_new = []
                        for asset in all_assets_names:
                            if asset in asset_response:
                                assets_identified_new.append(asset)
                        assets_identified = assets_identified_new#asset_response.strip().split(",")
                logger.info(f"assets_identified - {assets_identified}")
                if len(assets_identified)>0 and personalAssets==False:
                    asset_found = ",".join(assets_identified)
                    response = get_asset_based_response(assets_identified,question,token)
                    logger.info(f"get_asset_based_response - Response generated for assets:{assets_identified} which are from marketplace - {response}")
                    final_response = final_response + '\n' + response  
                elif len(assets_identified)>0 or personalAssets==True:
                    asset_found = ",".join(assets_identified)
                    prompt = f"""Below are asset details in which user has invested. 
                    Understand user's question carefully and provide answer using below mentioned details. 
                    Answer should be clear, and in positive and polite tone. Make sure answer is readable. 
                    If you are unable to answer then ask user to visit - 'https://uat.investor.evident.capital/portfolio/assets'
                    User's Trade:-{assets_identified[0]}
                    User's Commitments:-{assets_identified[1]}"""
                    response = get_gemini_response(question,prompt)
                    final_response = final_response + '\n' + response                    
                    logger.info(f"Response generated for assets:{assets_identified} in which user has invested - {response}")
                else:
                    response = search_on_internet(question)
                    final_response = final_response + '\n' + response  
                    asset_found = ''
            else:
                response = search_on_internet(question)
                asset_found = ''
                final_response = final_response + '\n' + response  
        if final_response == "":
            return "Sorry! I am unable understand the question. Can you provide more details so I can assist you better?", False
        final_response = get_gemini_response(final_response,"""Remove all repetitive statements while keeping all information intact.  
                                                    Maintain readability and ensure a proper structured response.  
                                                    DO NOT add any introductory statements like "Here's a summarized version..." or similar.  
                                                    Just return the cleaned-up text as the response.""")
        logger.info(f"Final Response - {final_response}")
    except Exception as e:
        logger.error(f"While generating answer from category based question following error occured - {str(e)}")
        final_response = "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at hello@evident.capital with the details of your query, and they’ll assist you promptly."
        asset_found = ''
    return final_response, asset_found, specific_category


# Get details of individual asset details
def get_specific_asset_details(asset_name,token): 
    try:
        all_asset_details = None
        # Investor assets
        url = "https://api-uat.evident.capital/asset/investor/list?page=1"
        payload = json.dumps({"name":f"{asset_name}"})

        headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }

        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        all_asset_details = data['data']
        logger.info(f"individual asset details - {all_asset_details}")
        return all_asset_details
    except Exception as e:
        logger.error(f"failed to get asset details - {str(e)}")
        return "No information found"


# Generate response based on provided asset specific detail
def get_asset_based_response(assets_identified,question,token):
    final_response = ''
    try:
        for ass in assets_identified:
            data = get_specific_asset_details(ass,token)
            note = """Ensure the response keeps the provided information intact without altering or modifying any details.
                    If certain information is unavailable, state politelyjust say "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at hello@evident.capital with the details of your query, and they’ll assist you promptly."
                    Else, Keep information as it is.
                    Avoid mentioning or implying that the user has provided or not provided information or response in requested format.
                    Do not greet the user in your response.
                    Use proper formatting such as line breaks to enhance readability while keeping answer as it is. Do NOT use any kind of formating like "*" just give proper line breaks using '\n'.
                    Maintain a positive and polite tone throughout the response.
                    Ask user to visit for more details - "https://uat.account.v2.evident.capital/" 
                    Note: The response should be clear, concise, and user-friendly, adhering to these guidelines. Encourage to ask more queries."""
            prompt = f"""Below is the asset details you have from Evident. Refer them carefully to generate answer. Check what kind of details user is asking about.
                To get proper trade values, add all results of that perticular assets. Do not provide paramters like id, and also create proper response it **SHOULD NOT** be in key value format.
                e.g. if you want overall records of units then it will be sum of all units of respective column, to get final unit counts add all values of units.
                NOTE - {note}
                Asset Details: - {data}"""
            response = get_gemini_response(question,prompt)      
            final_response = final_response + '\n'+ response  
        logger.info(f"asset based response - {final_response}")
    except Exception as e:
        logger.error(f"failed while handling asset based question - {str(e)}")
    return final_response


# Question handling flow - IP Count:9, OP Count:3
def handle_questions(token, last_asset, last_ques_cat, user_id, user_name, user_role, previous_questions, current_question, onboarding_step):     
    asset_found = ''
    response = ''
    isRelated = False
    isAssetRelated = False

    # Check if question is in context of current question or not if this is not fresh conversation
    if len(previous_questions)>=1:        
        prompt = f"""Identify if current question is related or is in context of previous questions.
                    Asset Names - {last_asset}
                    Previous Questions - {previous_questions}
                    If current question is in context or related to previous question then RETURN 1.
                    Else STRICTLY RETURN 0.
                    Note - Strictly revert in way specified above. DO NOT add or create response in any other way or format."""
        question_related = get_gemini_response(current_question,prompt)
        
        try:
            if int(question_related.strip())==1 and last_asset=='':
                isRelated = True
            elif int(question_related.strip())==1 and last_asset!='':
                isRelated = True
                isAssetRelated = True     
            logger.info(f"Question is related to previous question status is - {isRelated}")                   
        except Exception as e:
            logger.error(f"Failed to check if question is related to previous question or not, following error occured - {str(e)}")

    # Identify question's category
    promp_cat = get_prompt_category(current_question,user_role)
    promp_cat = promp_cat.split(",")
    promp_cat = [p.strip() for p in promp_cat]
    
    # If question is just a greeting nothing else is asked in that question
    if 'Greetings' in promp_cat[0] and len(promp_cat)==1:
        prompt = f"""User name is - {user_name}, reply to user in polite and positive way. Encourage for further communication."""
        response = get_gemini_response(current_question,prompt)
        return response,'','Greetings'
    # Remove greetings category from prompt categories
    else:
        promp_cat = [p.strip() for p in promp_cat if 'Greetings' not in p.strip()]

    response,asset_found,specific_category = category_based_question(current_question,previous_questions,promp_cat,token,user_id,onboarding_step,isRelated,isAssetRelated,last_asset, last_ques_cat)
    logger.info(f"final response from handle_questions - {response}")
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
    "email": "sai.mansanpally+0402cpi@evident.capital",
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
    # print(response, data)
    token = data['token']
    # 2FA
    twoFA_url = "https://api-uat.evident.capital/user/two-factor-authentication"
    payload = json.dumps({
            "code": "123456",
            "ipAddress": "127.0.0.1"
            })
    headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
    response = requests.request("POST", twoFA_url, headers=headers, data=payload)
    data = response.json()
    # print(data)
    if data['code']=='2FA_VERIFIED':
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
        # print(data)
    return JsonResponse({"token":token},status=200)


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
            if len(previous_questions)==2:
                update_chat_title(current_question,chat_session_id)
                
            response, current_asset, current_ques_cat = handle_questions(token, last_asset, last_ques_cat, user_id, user_name, user_role, previous_questions, current_question, onboarding_step)
            html_content = markdown.markdown(response)
            response = html_content
            # logger.info(f"After HTML markup from main function - {response}")
            # print("current_ques_cat- ",current_ques_cat)
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
