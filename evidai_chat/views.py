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

def hello_world(request):
    return JsonResponse({"message":"Request received successfully","data":[],"status":True},status=200)


@csrf_exempt 
def get_gemini_response(question,prompt):
        try:
            prompt = "Your name is EvidAI a smart intelligent bot to provide customer support and help them."+ prompt
            model = genai.GenerativeModel('gemini-pro')
            response_content = model.generate_content([prompt, question])
            return response_content.text.strip()
        except Exception as e:
            logger.critical(f'Failed to get answer from gemini due to - {str(e)}')
            response = "Sorry! I am not able to find answer for your question. \nRequest you to coordinate with our support team on - hello@evident.capital.\nThank You."
            return response
    

def get_prompt_category(question):
    prompt = f"""Based on user's question and context, identify what is the category of this question from below mentioned categories And STRICTLY PROVIDE ONLY NAME OF CATEGORIES NOTHING ELSE, IF NO CATEGORY MATCHES THEN RETURN "FAILED" -
                 USER's QUESTION - {question}
                 Greetings: Formal or friendly greetings. Hi hello or any other generic greetings.
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
                 Assets_Creation: Detailed step by step process only to create assets. 
                 Asset_Managers:This category contains information about EVIDENT's due diligence process for asset managers, the structuring and tokenization of assets, and the various fundraising methods available on the platform, emphasizing efficiency, transparency, and investor protection.
                 Onboarding_Distributor:Step by step process for distributor onboarding process
                 Onboarding_Issuer:Step by step process for issuer onboarding process
                 Corp_Investor_Onboarding:Step by step process for Corp investor onboarding process
                 Onboarding_Investor:Step by step process for investor onboarding process
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
                 """
    response = get_gemini_response(question,prompt)
    # print(response)
    return response


# Authenticate from jwt token we are getting from UI
@csrf_exempt
def token_validation(token):    
    # print(token)
    try:
        # Validate token 
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
        roles = [role['name'] for role in data['user']['roles']]
        onboarding_details = data['user']['individualOnboarding']
        onboarding_steps = []
        for stp in onboarding_details:
            temp_stp = {}
            temp_stp['stepName'] = stp['stepName']
            temp_stp['stepStatus'] = stp['stepStatus']     
            onboarding_steps.append(temp_stp)       
        
        if validate:
            return token,user_id,user_name,roles,onboarding_steps
        else:
            return None, None, None, None, None
    except:
        return None, None, None, None, None

@csrf_exempt
def add_to_conversations(user_id,chat_session_id,question, answer, is_asset):
    try:
        # Get the current date and time in UTC
        current_datetime = datetime.now(timezone.utc)

        # Convert to ISO 8601 format
        iso_format_datetime = current_datetime.isoformat()
        new_conv = models.Conversation.objects.create(
            user_id=user_id,
            chat_session_id=chat_session_id,
            question=question,
            answer=answer,
            created_at=iso_format_datetime,
            updated_at=iso_format_datetime,
            is_asset = is_asset
        )
        new_conv.save()
        return new_conv.id  
    except Exception as e:
        logger.error(f'Failed to add conversation for user_id={user_id}, chat_session_is={chat_session_id},question={question},and answer={answer} due to - '+str(e))
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


def get_conversation_for_context(chat_session_id):
    all_convo = models.Conversation.objects.filter(chat_session_id=chat_session_id).order_by('-id')
    convo_list = [
                {"question": convo.question,
                "answer":convo.answer}
                for convo in all_convo
            ]
    questions = [q.question for q in all_convo]
    return convo_list, questions


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
#     if request.method == 'GET':
#         # Render the HTML page for GET requests
#         return render(request, 'evidentchatbot.html') 
    

def search_on_internet(question):
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
    return response


def general_cat_based_question(prev_related,Asset_Related,user_name,questions,promp_cat,token,roles,onboarding_step):
    logger.info(f"In general cat based area data - {prev_related,Asset_Related,user_name,questions,promp_cat,token,roles,onboarding_step}")
    question = questions[0]
    final_response = ""
    asset_found = False
    promp_cat_new = ",".join(promp_cat)
    specific_category = promp_cat_new.replace("_",' ').split(',')  # Replace with the desired category
    logger.info(f"specific_category")
    for promp_cat in specific_category:   
        logger.info(f"promp_cat at 453 - {promp_cat}")       
        if promp_cat!='FAILED' and promp_cat !='Personal Assets':
            logger.info("461")
            try:
                data = models.BasicPrompts.objects.filter(prompt_category=promp_cat)
                prompt_data_list = []
                for d in data:
                    prm = d.prompt
                    if 'Onboarding' in promp_cat:
                        logger.info("468")
                        prm = f'{prm} \nUser\'s current onboarding status - {onboarding_step}'
                    prompt_data_list.append(prm)
                logger.info(prompt_data_list)
                prompt_data = f"""Customer:{user_name} is not providing you any information, all information is with you, DO NOT SAY TO CUSTOMER THAT THEY HAVE NOT PROVIDED INFORMATION,INSTEAD SAY YOU DONT HAVE INFORMATION CURRENTLY ON THIS. You are smart and intelligent chat-bot having good knowledge of finance sector considering this chat with user. 
                Provide answer in a way that you are chatting with customer. Do not use any kind of emojis. Do not greet user while answering. Guide and help user to finish their steps and complete onboarding. Use below information to get answer -
                {prompt_data_list}
                NOTE - If you are not able to find answer then say "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at hello@evident.capital with the details of your query, and they’ll assist you promptly."
                Keep tone positive and polite while answering user's query. Do NOT use any kind of formating like "*" just give proper line breaks using '\n'"""
                response = get_gemini_response(question,prompt_data)
                logger.info(477)
                final_response = final_response + '\n' + response    
                logger.info(478)
            except Exception as e:
                logger.info(f"482 - {str(e)}")
                prm = """For this topic currently we don't have any information. 
                Provide answer in a way that "I’m sorry I couldn’t assist you right now. 
                However, our support team would be delighted to help! Please don’t hesitate to email 
                them at hello@evident.capital with the details of your query, and they’ll assist you promptly." 
                this will cover the part of question for which information is not available"""
                final_response = get_gemini_response(question,prm)
                logger.info("489")
        elif promp_cat=='FAILED':
            logger.info("491")
            response = search_on_internet(question)
            asset_found = False
            final_response = final_response + '\n' + response   
        elif 'Personal Assets' in promp_cat or (Asset_Related==True and prev_related==True):    
            logger.info("Asset related - 496")    
            # Can i directly take from DB? API is taking too long
            all_assets_names = get_asset_list(token,roles)
            logger.info(f"Got asset list - {all_assets_names}")
            prompt = f"""Identify if question is about any specific asset or its user wants to know about all assets present for him/her.
                        If question is about specific assets then STRICTLY ONLY return Name of that asset from below asset list, if there is more than one asset then separate them with coma(,). E.g. openai,
                        else if question is about generically all the assets then retun 1, else return 0.
                        Asset List - {all_assets_names}
                        Examples:-
                        Question: what is commitment status of my assets?
                        Answer: 1
                        Question: what is minimum investment amount for Keith Haring?
                        Answer:Keith Haring - Untitled
                        Question: what are highlights of mumbai
                        Answer: 0""" 
            asset_response = get_gemini_response("".join(questions),prompt)
            logger.info(f"asset_response - {asset_response}")
            try:
                if int(asset_response.strip())==1:
                    assets_identified = all_assets_names
                elif int(asset_response.strip())==0:
                    assets_identified = ''
            except:    
                assets_identified = asset_response.strip().split(",")
                logger.info(f"assets_identified - {assets_identified}")
                if len(assets_identified)>0:
                    asset_found=True
                    response = get_asset_based_response(user_name,assets_identified,question,token)
                    logger.info(f"get_asset_based_response - {response}")
                    final_response = final_response + '\n' + response  
                else:
                    logger.info(527)
                    response = search_on_internet(question)
                    final_response = final_response + '\n' + response  
                    asset_found = False
        else:
            logger.info(532)
            response = search_on_internet(question)
            asset_found = False
            final_response = final_response + '\n' + response  
    if final_response == "":
        return "Sorry! I am unable understand the question. Can you provide more details so I can assist you better?", False
    return final_response, asset_found


def get_asset_list(token,roles): 
    all_asset_details = None
    roles = [role.strip() for role in roles]
    all_asset_names = []
    # Investor assets
    url = "https://api-uat.evident.capital/asset/investor/list?page=1"

    payload = {}
    headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

    response = requests.request("POST", url, headers=headers, data=payload)
    data = response.json()
    page_numbers = data['meta']['last_page_url'].split("=")[-1]
    all_asset_details = data['data']
    for p in range(2, int(page_numbers)+1):
        url = f"https://api-uat.evident.capital/asset/investor/list?page={str(p)}"
        payload = {}
        headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        all_asset_details = all_asset_details + data['data']

    for names in all_asset_details:
        name = names['name']
        all_asset_names.append(name)
    return all_asset_names


def get_specific_asset_details(asset_name,token):   
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
    return all_asset_details


def get_asset_based_response(user_name,assets_identified,question,token):
    # print("Inputs - ",user_name,assets_identified,question,token)
    assets = []
    final_response = ''
    for ass in assets_identified:
        data = get_specific_asset_details(ass,token)
        assets.append(data)
        # print("get_specific_asset_details - ",assets)
        note = """Ensure the response keeps the provided information intact without altering or modifying any details.
                If certain information is unavailable, state politelyjust say "I’m sorry I couldn’t assist you right now. However, our support team would be delighted to help! Please don’t hesitate to email them at hello@evident.capital with the details of your query, and they’ll assist you promptly."
                Else, Keep information as it is.
                Avoid mentioning or implying that the user has provided or not provided information or response in requested format.
                Do not greet the user in your response.
                Use proper formatting such as line breaks to enhance readability while keeping answer as it is. Do NOT use any kind of formating like "*" just give proper line breaks using '\n'.
                Maintain a positive and polite tone throughout the response.
                Note: The response should be clear, concise, and user-friendly, adhering to these guidelines."""
        prompt = f"""Below is the asset details you have from Evident. Refer them carefully to generate answer. Check what kind of details user is asking about.
            To get proper trade values, add all results of that perticular assets. 
            e.g. if you want overall records of units then it will be sum of all units of respective column, to get final unit counts add all values of units.
            NOTE - {note}
            Asset Details: - {assets}"""
        response = get_gemini_response(question,prompt)      
        final_response = final_response + response  
    return final_response


def handle_questions(token, roles, user_name, questions,onboarding_step):     
    asset_found = False
    response = ''
    question = questions[0]
    prev_related = False
    # print("question - ",question)
    # Identify question
    promp_cat = get_prompt_category(question)
    promp_cat = promp_cat.split(",")
    promp_cat = [p.strip() for p in promp_cat]
    FAILED = False
    Asset_Related = False
    # print("promp_cat - ",promp_cat)
    # If question is just a greeting nothing else is asked in that question
    if 'Greetings' in promp_cat[0] and len(promp_cat)==1:
        prompt = f"""User name is - {user_name}, reply to user in polite and positive way."""
        response = get_gemini_response(question,prompt)
        return response,False
    # Remove greetings category from prompt categories
    else:
        promp_cat = [p for p in promp_cat if 'Greetings' not in p]

    if FAILED and len(questions)>1:
        prompt = f"""Check if current question is related or is in context of previous questions then return 0.
        If current question is related or in context to assets by reffering previous questions then return 1. Previous questions - {questions}"""
        response = get_gemini_response(question,prompt)
        try:
            if int(response.strip())==1:
                Asset_Related=True
            else:
                prev_related=True
        except:
            pass
    else:
        Asset_Related = True
    # print("Asset_Related - ",Asset_Related, "\nprev_related - ",prev_related)
    response,asset_found = general_cat_based_question(prev_related,Asset_Related,user_name,questions,promp_cat,token,roles,onboarding_step)
    
    return response,asset_found


@csrf_exempt
def login(request):
    # print("in login")
    url = "https://api-uat.evident.capital/user/login"
    payload = json.dumps({
    "email": "sai.mansanpally+2801issuer@evident.capital",
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
    data = response.content

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
            token_valid,user_id,user_name,roles,onboarding_step = token_validation(token)
            if token_valid is None:
                logger.error(f"Invalid Token, Token: {token}")            
                return JsonResponse({"message":"Invalid user, please login again","data":{"response":"Failed to validate token for user, please check token"},"status":False},status=400)
            
            data = json.loads(request.body)
            question = data.get('question')
            chat_session_id = int(data.get('chat_session_id'))

            # chat session validation
            chat_session_validation = validate_chat_session(chat_session_id)
            if chat_session_validation is None:
                logger.error(f'Invalid chat session, kindly create new chat session for user ID - {user_id}')
                return JsonResponse({"message":"Unexpected error occured","data":{
                "response":"Invalid chat session, kindly create new chat session"},"status":False},status=200)
            
            conversation_history, questions = get_conversation_for_context(chat_session_id)

            # Update title
            if len(conversation_history)==2:
                update_chat_title(question,chat_session_id)
                
            questions.insert(0,question)
            # print(questions)
            response, asset_found = handle_questions(token, roles, user_name, questions,onboarding_step)
            html_content = markdown.markdown(response)
            response = html_content
                        
            add_to_conversations(user_id,chat_session_id,question,response,asset_found)      
            
            return JsonResponse({"message":"Response generated successfully","data":{
                                    "response":response},"status":True},status=200)
        
        else:
            logger.error('Invalid method request, POST method is expected.')
            return JsonResponse({"message":"Unexpected error occurred","data":{
                "response":"Invalid method request, POST method is expected."},"status":False},status=400)
    except Exception as e:
        logger.error(f"Error occured from main function - {str(e)}")
        return JsonResponse({"message":"Unexpected error occured","data":{
                "response":''},"status":False},status=400)

