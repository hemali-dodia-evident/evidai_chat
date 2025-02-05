import google.generativeai as genai
import os
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import datetime,timezone
from . import models
import logging
import hashlib
import secrets
from elasticsearch import Elasticsearch
from django.shortcuts import render
from django.db.models.functions import Lower

# Define the connection settings
host_ip = os.environ['ES_HOST_NAME']
# print(host_ip)

es = Elasticsearch(hosts=[{'host': f'{host_ip}', 'port': 9200, 'scheme': 'http'}])  # Increased timeout 
# print("es - ",es.health_report())
index_name = os.environ['EL_IDX_NAME']#"evid_prompts_new"

# Load pre-trained model and tokenizer
# tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
# model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')

key = os.environ["GOOGLE_API_KEY"]
genai.configure(api_key=f"{key}")

# Load the model
# model = SentenceTransformer('paraphrase-MiniLM-L6-v2')


assets = ['anthropic','canva','databricks','deel','discord','epic games','epic-games','groq','kraken',
'openai', 'open ai', 'open-ai', 'plaid', 'revolut', 'shein', 'spacex','space-x', 'spece x', 'stripe', 
'xai', 'x ai', 'x-ai']


# Configure the logging settings
logging.basicConfig(
    filename='application.log',         # File to save logs
    level=logging.INFO,                 # Log level
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log message format
    datefmt='%Y-%m-%d %H:%M:%S'         # Date format
)


def log_message(level, message):
    """
    Logs a message with a specified level and the current date and time.
    
    Args:
        level (str): The log level ('info', 'warning', 'error', etc.).
        message (str): The message to log.
    """
    logger = logging.getLogger()

    if level.lower() == 'info':
        logger.info(message)
    elif level.lower() == 'warning':
        logger.warning(message)
    elif level.lower() == 'error':
        logger.error(message)
    elif level.lower() == 'critical':
        logger.critical(message)
    else:
        logger.debug(message)  # Default to debug level for unknown levels


def hello_world(request):
    return JsonResponse({"message":"Request received successfully","data":[],"status":True},status=200)


def find_most_relevant_prompt(question):
    search_query = {
        "query": {
            "multi_match": {
                "query": question,
                "fields": [
                    "prompt_category^3",
                    "asset_name^5",
                    "asset_sub_cat^4",
                    "prompt^5"
                ]
            }
        },
        "sort": [
                { "_score": { "order": "desc" } }
            ]        
    }

    response = es.search(index=index_name, body=search_query)
    
    selected_prompt = response['hits']['hits']
    # print("Selected Prompt -",type(selected_prompt),len(selected_prompt))
    prm = ""
    for i in selected_prompt:
        print("SCORES - ",i['_score'])
        prm = prm+'\n'+i['_source']['prompt']
    # print("*******************************Prompts********************************")
    # print(prm)
    # print("*******************************Prompts********************************")
    return prm
    

@csrf_exempt 
def get_gemini_response(question,prompt):
        try:
            model = genai.GenerativeModel('gemini-pro')
            response_content = model.generate_content([prompt, question])
            return response_content.text.strip()
        except Exception as e:
            log_message('critical','Failed to get answer from gemini due to - '+str(e))
            response = "Sorry! I am not able to find answer for your question. \nRequest you to coordinate with our support team on - hello@evident.capital.\nThank You."
            return response
    

def get_prompt_category(question):
    prompt = f"""Based on user's question and context, identify what is the category of this question from below mentioned categories And PROVIDE ONLY NAME OF CATEGORIES NOTHING ELSE, IF NO CATEGORY MATCHES THEN RETURN "FAILED" -
                 USER's QUESTION - {question}
                 Assets_Creation: Detailed step by step process to create assets
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
                      Bot: FAILED
                 """
    response = get_gemini_response(question,prompt)
    return response


@csrf_exempt
def create_token(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_id = data.get("user_id")
        random_seed = secrets.token_hex(32) 
        token = hashlib.sha256(random_seed.encode()).hexdigest()
        # Save the user_id and token to the UserChatLogin model
        user_chat_login, created = models.UserChatLogin.objects.update_or_create(
            user_id=user_id,
            defaults={'token': token},
        )
        return JsonResponse({"message":"Token generated successfully",
                             "data":[{'token': token}],
                             "status":True},status=200)

    else:
        return JsonResponse({
            "message": "Invalid JSON format",
            "status": False,
            "data": {"response":''}
        }, status=200)


@csrf_exempt
def token_validation(token):
    try:
        validate = models.UserChatLogin.objects.get(token=token)
        if validate:
            return token
        else:
            return       
    except:
        return


@csrf_exempt
def add_to_conversations(token,chat_session_id,question, answer, is_asset):
    try:
        # Get the current date and time in UTC
        current_datetime = datetime.now(timezone.utc)

        # Convert to ISO 8601 format
        iso_format_datetime = current_datetime.isoformat()
        new_conv = models.Conversation.objects.create(
            token=token,
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
        log_message('error',f'Failed to add conversation for token={token}, chat_session_is={chat_session_id},question={question},and answer={answer} due to - '+str(e))
        return None  


# Get previous conversation as context
def get_contextual_input(conversation_history, max_length=1000):
    contextual_input = '\n'.join(set(f"User_Question: {entry['question']}" for entry in conversation_history))
    return contextual_input[-max_length:]


# Get all chat session based on user
@csrf_exempt
def get_chat_session_details(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        token = data.get('token')
        try:
            chats = models.ChatSession.objects.filter(token=token,show=True)
            all_convo = {}
            for chat in chats:  # Iterate over each ChatSession object in the QuerySet
                all_convo["id"] = chat.id
                all_convo["title"] = chat.title  # Access the 'title' field of each chat
                
            return JsonResponse({"message":"All chat sessions fetched successfully",
                                "data":[{"response":all_convo}],"status":True},status=200)
        except Exception as e:
            log_message('error',str(e))
            return JsonResponse({"message":"No chat sessions found",
                                "data":[{"response":[]}],"status":True},status=200)
    else:
        return JsonResponse({
            "message": "Invalid JSON format",
            "status": False,
            "data": {"response":''}
        }, status=200)


# Create Session
@csrf_exempt 
def create_chat_session(request):
    logging.info("Received request: %s", request.body)
    try:
        # Parse JSON data from request body
        data = json.loads(request.body)
        
        # Extract required fields from data
        token = data.get('token')

        # Get the current date and time in UTC
        current_datetime = datetime.now(timezone.utc)

        # Convert to ISO 8601 format
        iso_format_datetime = current_datetime.isoformat()
        # Create a new ChatSession instance
        new_chat_session = models.ChatSession.objects.create(
            token=token,
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
                'token': new_chat_session.token,
                'title': new_chat_session.title,
                'created_at': new_chat_session.created_at,
                'updated_at': new_chat_session.updated_at,
            }
        }, status=200)

    except json.JSONDecodeError:
        log_message('error','Invalid JSON format')
        return JsonResponse({
            "message": "Invalid JSON format",
            "status": False,
            "data": {"response":''}
        }, status=200)
    

# Update title of newly created chat session
@csrf_exempt
def update_chat_title(question,chat_session_id):
    prompt = "Based on this question generate relative title for this conversation. Title should be short, it should not exceed 50 characters."
    # Get the current date and time in UTC
    current_datetime = datetime.now(timezone.utc)

    # Convert to ISO 8601 format
    iso_format_datetime = current_datetime.isoformat()
    title = get_gemini_response(question,prompt)
    
    try:
        chat_session = models.ChatSession.objects.get(id=chat_session_id)
        chat_session.title = title
        chat_session.updated_at = iso_format_datetime
        chat_session.save()
        return title
    except Exception as e:
        log_message('error',str(e))
        return 


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
        data = json.loads(request.body)
    
        chat_session_id=data.get('chat_session_id')
        chat_present = models.ChatSession.objects.get(id=chat_session_id)
        if chat_present.show ==True:
            try:
                all_convo = models.Conversation.objects.filter(chat_session_id=chat_session_id)
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
                return JsonResponse(response_data,status=200)
            except Exception as e:
                log_message('error',str(e))
                return JsonResponse({"message": "Unexpected error occurred.",
                    "status": False,
                    "dcata": {
                        "response":"Unable to get Conversations, Please try again."
                    }},status=200)
        else:
            return JsonResponse({
                "message":"Failed to get conversations",
                "data":{"response":"Failed to get conversation details, please check if correct chat session id is passed."},
                "status":False
            },status=200)
    else:
        log_message('error', "Failed to get conversation. Invalid method, POST method is expected")
        return JsonResponse({
            "message": "Unexpected error occurred.",
            "status": False,
            "data": {'response':'Invalid method, POST method is expected'}
        }, status=200)


# Validate chat session id if it is active or not
def validate_chat_session(chat_session_id):
    try:
        chat_session_id=chat_session_id
        chat_session = models.ChatSession.objects.get(id=chat_session_id)
        return chat_session
    except Exception as e:
        log_message('error', "Failed to validate chat session due to - "+str(e))
        return 


# Delete Chat session
@csrf_exempt
def delete_chat_session(request):
    if request.method=="POST":
        data = json.loads(request.body)
        chat_session_id = data.get("chat_session_id")
        try:
            chat = models.ChatSession.objects.get(id=chat_session_id)
            chat.show = False
            chat.save()
        except Exception as e:
            log_message('error',str(e))
            return JsonResponse({"message":"Failed to delete Chat session","data":{"response":"Please check if correct chat session id is passed."},"status":False},status=200)
        return JsonResponse({"message":"Chat session deleted successfully","data":{
            "chat_session_id":chat_session_id, "title":chat.title},"status":True},status=200)
    else:
        log_message('error','Invalid JSON format')
        return JsonResponse({"message":"Invalid request type, POST method is expected","data":[],"status":False},status=200)

    
@csrf_exempt
def delete_multiple_chat_session(request):
    if request.method=="POST":
        data = json.loads(request.body)
        chat_session_id = data.get("chat_session_id")
        deleted_sessions = {}
        try:
            for chats in chat_session_id:
                chat = models.ChatSession.objects.get(id=chats)
                chat.show = False
                chat.save()
                deleted_sessions['chat_session_id']=chats
                deleted_sessions['title']=chat.title
        except Exception as e:
            log_message('error',str(e))
            return JsonResponse({"message":"Failed to delete Chat session","data":[],"status":False},status=200)
        return JsonResponse({"message":"Chat session deleted successfully","data":deleted_sessions,"status":True},status=200)
    else:
        log_message('error','Invalid JSON format')
        return JsonResponse({"message":"Invalid request type, POST method is expected","data":[],"status":False},status=200)


@csrf_exempt
def chat_page(request):
    if request.method == 'GET':
            # Render the HTML page for GET requests
            return render(request, 'evidentchatbot.html') 
    

def check_asset(questions):
    asset_found = False
    asset = set()
    for ques in questions:
        ques = "".join(ques.lower().split())
        for ass in assets:
            if ass in ques:
                asset.add(ass)
                asset_found = True
    print("ass - ",asset)    
    return asset_found,asset


def asset_based_questions(specific_category,sb,question):
    prompt_data = []
    data = models.BasicPrompts.objects.filter(prompt_category=specific_category,  # Exact match for prompt_category
                                                asset_name__icontains=sb)
    for d in data:
        prompt_data.append(d.prompt)
    prompt_data = "IF YOU ARE NOT ABLE TO FIND ANSWER IN THIS PROMPT THEN JUST RETURN 'FAILED'.\n".join(prompt_data)
    ans_cat = get_gemini_response(question,prompt_data)
    print('at line 458')
    if ans_cat == 'Sorry! I am not able to find answer for your question. \nRequest you to coordinate with our support team on - hello@evident.capital.\nThank You.':
        ans_cat = ''
        print('at line 461')
    return ans_cat


def general_cat_based_question(question,chat_session_id):
    promp_cat = get_prompt_category(question)
    specific_category = promp_cat.replace("_",' ').split(',')  # Replace with the desired category
    print("PROMPT CATEGORY - ", specific_category)
    check_cat = specific_category[0]
    print("check_cat - ",check_cat)
    if check_cat != 'FAILED':
        print("at line - 471")
        Answer_Cat = []
        for spc_cat in specific_category:
            prompt_data = []
            data = models.BasicPrompts.objects.filter(prompt_category=spc_cat)
            # print("PROMPT DATA FETCHED FROM DATABASE - \n",data.values)
            for d in data:
                prompt_data.append(d.prompt)
            prompt_data = "IF YOU ARE NOT ABLE TO FIND ANSWER IN THIS PROMPT THEN JUST RETURN EMPTY SPACE like ' '.\n".join(prompt_data)
            ans_cat = get_gemini_response(question,prompt_data)
            if ans_cat == 'Sorry! I am not able to find answer for your question. \nRequest you to coordinate with our support team on - hello@evident.capital.\nThank You.':
                ans_cat = ''
            Answer_Cat.append(ans_cat)
        response = "\n".join(Answer_Cat)
    else:
        print("at line - 486")
        asset_found,substring = check_asset(question,chat_session_id)
        if asset_found:
            print("at line - 489")
            specific_category = "Existing Assets"  
            Answer_Cat = []
            for sb in substring:
                print("at line - 493")
                ans_cat = asset_based_questions(specific_category,sb,question)
                if ans_cat != 'FAILED':
                    print("at line - 496")
                    Answer_Cat.append(ans_cat)
                else:
                    print("at line - 499")
                    Answer_Cat.append('')
        else:
            print("at line - 502")
            response = get_gemini_response(question,'Chat with user, provide all information you can, support them, resolve their queries if they have. Be nice and sweet along with inteligent while chatting. If its greeting text then simply greet them and ask how you can help them. Keep asnwer short not too long. And tell user that this information is from internet when user is not greeting.')
    return response


def handle_questions(questions,chat_session_id):
    asset_found = False
    question = questions[-1]
    asset_found,substring = check_asset(questions,chat_session_id)
    print("substring - ",substring)
    print("asset_found - ",asset_found)
    if asset_found:
        specific_category = "Existing Assets"  
        Answer_Cat = []
        print("at line - 516")
        for sb in substring:
            ans_cat = asset_based_questions(specific_category,sb,question)
            if ans_cat != 'FAILED':
                print("at line - 519")
                Answer_Cat.append(ans_cat)
            else:
                print("at line - 521")
                response = general_cat_based_question(question,chat_session_id)
                asset_found = False
                return response,asset_found
        response = "\n".join(Answer_Cat)
        print("At line 529")
    else:
        print("at line - 526")
        response = general_cat_based_question(question,chat_session_id)
    return response,asset_found


# Main flow
@csrf_exempt
def evidAI_chat(request):
    try:
        log_message('info', 'Inside Try method of evidAI_chat function, request received successfully.')
        if request.method == 'POST':
            print("STEP 1 - REQUEST RECEIVED")
            data = json.loads(request.body)
            question = data.get('question')
            chat_session_id = int(data.get('chat_session_id'))
            token = data.get('token')
            log_message("info",f"all param received - Qestion: {question}, Chat session ID: {chat_session_id}, Token: {token}")
            # Validate token
            token_valid = token_validation(token)
            if token_valid is None:
                log_message("error",f"Invalid Token, Token: {token}")            
                return JsonResponse({"message":"Invalid user, please login again","data":{"response":"Failed to validate token for user, please check token or user_id"},"status":False},status=200)
            
            # chat session validation
            chat_session_validation = validate_chat_session(chat_session_id)
            if chat_session_validation is None:
                log_message('error', 'Invalid chat session, kindly create new chat session')
                return JsonResponse({"message":"Unexpected error occured","data":{
                "response":"Invalid chat session, kindly create new chat session"},"status":False},status=200)
            print("STEP 2 - ALL DATA VALIDATED")
            
            # Update title
            try:
                models.Conversation.objects.get(chat_session_id=chat_session_id)                                    
            except:
                update_chat_title(question,chat_session_id)
            response = None
            conversation_history, questions = get_conversation_for_context(chat_session_id)
            print("STEP  3 - GOT CONVERSATION HISTORY :- ",conversation_history,"\nLIST OF QUESTIONS :- ",questions)

            if len(conversation_history)==0:
                """Fresh conversation"""
                questions = [question]
                response, asset_found = handle_questions(questions,chat_session_id)
                
            else:
                """Ongoing conversations"""
                questions.append(question)
                response, asset_found = handle_questions(questions, chat_session_id)
            
            add_to_conversations(token,chat_session_id,question,response,asset_found)      
            # print("RESPONSE GENERATED - ",response)
            return JsonResponse({"message":"Response generated successfully","data":{
                                    "response":response},"status":True},status=200)
        else:
            log_message('error', 'Invalid method request, POST method is expected.')
            return JsonResponse({"message":"Unexpected error occurred","data":{
                "response":"Invalid method request, POST method is expected."},"status":False},status=200)
    except Exception as e:
        log_message('error', str(e))
        return JsonResponse({"message":"Unexpected error occured","data":{
                "response":str(e)},"status":False},status=200)

