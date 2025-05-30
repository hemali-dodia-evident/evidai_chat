import google.generativeai as genai
import os
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import datetime,timezone
from . import models
import logging
import requests
from . import views



# Configure the logging settings
logger = logging.getLogger(__name__)


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


# Get details of individual asset details
def get_specific_asset_details(asset_name,token,domain): 
    try:
        all_asset_details = None
        # Investor assets
        url = f"https://{domain}/asset/investor/list?page=1"
        payload = json.dumps({"name":f"{asset_name.strip()}"})

        headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }

        response = requests.request("POST", url, headers=headers, data=payload)
        data = response.json()
        try:
            # logger.info(f"got asset information - {data}")
            all_asset_details = data['data'][0]
        except:
            logger.info(f"failed to get asset info - {data}")
            return "Asset is not available at Marketplace", "Not available", None
        
        visibility = all_asset_details['visibility'][0]+all_asset_details['visibility'][1:].lower()
        # print("visibility - ",visibility)
        if visibility == 'Exclusive':
            asset_info = "This is an Exlusive Asset, I can not directly provide details. To access this asset related information kindly visit Marketplace. Search for this asset in searchbar. Enter Access Code to view this asset."
            return asset_info, ''
        retirementEligible = 'Not Available'
        if all_asset_details['retirementEligible'] == False:
            retirementEligible = 'Asset is not retairement elgible.'
        else:
            retirementEligible = 'Asset is retairement elgible.'
        # asset_url = all_asset_details['shortUrl']
        # print("Retairment eligibility - ",retirementEligible)
        investment_details = ''
        if all_asset_details['investmentMode']=='Commitment':
            # print("Asset is in commit mode")
            if all_asset_details['commitmentDetails'] != []:
                commitmentDetails = all_asset_details['commitmentDetails'][0] 
                # print("Commitment details - ",commitmentDetails)   
                commitmentStatus = commitmentDetails['status'].replace("_"," ") 
                startDate = commitmentDetails['startAt'].split("T")[0] if commitmentDetails['startAt'] is not None or commitmentDetails['startAt'] !='' else ''
                endDate = commitmentDetails['endAt'].split("T")[0] if commitmentDetails['endAt'] is not None or commitmentDetails['endAt'] !='' else ''
                investment_details = f"""
                Commitment Status - {commitmentStatus}
                Target Amount - {str(commitmentDetails['targetAmount'])}
                Minimum Investment Amount - {str(commitmentDetails['minimumAmount'])}
                Maximum Investment Amounr - {str(commitmentDetails['maximumAmount'])}
                Raised Amount - {str(commitmentDetails['raisedAmount'])}
                Start On - {startDate}
                End On - {endDate}"""
            else:
                commitmentDetails = "The commitment details of this asset will come soon. This asset is not active yet to perform commitment."
        elif all_asset_details['investmentMode']=='Trading':
            # print("Asset is in trade mode")
            tardeDetails = all_asset_details['investmentDetails']
            investment_details = f"""Open Offers - {tardeDetails['openOffers']}
            Number of Investors - {tardeDetails['numberOfInvestors']}
            Total invested amount - {tardeDetails['totalInvested']}"""
        # print("Investment Details - ",investment_details)
        updates_details = all_asset_details['updates']
        updates = ""
        if updates_details !=[]:
            for u in updates_details:
                updates = f"Title: {u['title']}\nDescription: {u['description']}\n"
        else:
            updates = "Will notify as soon as there is any new update!"
        # print("Updates - ",updates)
        keyHighlights = "Key highlights are - "
        try:
            knum = 1
            for kh in all_asset_details['assetKeyHighlights']:
                keyHighlights = keyHighlights+str(knum)+'.'+kh['text']+'\n'
                knum+=1
        except:
            keyHighlights = "No highlights are present..."
        # print("Keyhighlights - ",keyHighlights)
        rateOfReturn = all_asset_details['rateOfReturn'] if all_asset_details['rateOfReturn'] is not None else ''
        # print("rate of return -", rateOfReturn)
        exitStrategy = all_asset_details['exitStrategy'] if all_asset_details['exitStrategy'] is not None else ''
        # print("Exit strategy - ",exitStrategy)
        manager = ''
        try:
            manager = "Asset manager is "+all_asset_details['manager']['kyc']['firstName'][0]+all_asset_details['manager']['kyc']['firstName'][1:].lower()+' '+all_asset_details['manager']['kyc']['lastName'][0]+all_asset_details['manager']['kyc']['lastName'][1:].lower()
        except:
            manager = ''
        # print("manager - ",manager)
        company = ""
        try:
            company = f"Company name is {all_asset_details['manager']['company']['companyName']}"
        except:
            company = ""
        # print("Comapny - ",company)
        impact_details = "These are impacts of this asset - "
        try:
            impacts = all_asset_details['impacts']
            immpct = []
            for imp in impacts:
                immpct.append(imp['name'])
            immpct = ", ".join(impacts)
            impact_details = impact_details+immpct
        except:
            impact_details = "No impacts!!!"
        # print("Impact details - ",impact_details)
        
        status = "Asset status - "
        try:
            status = status + all_asset_details['status'][0].upper()+all_asset_details['status'][1:].lower()
        except:
            status = ""
        # print("status - ",status)
        asset_id = data['data'][0]['id']
        try:
            url = f"https://{domain}/event/get-events-by-asset"
            payload = json.dumps({
            "assetId": asset_id
            })
            headers = {
                        'Authorization': f'Bearer {token}',
                        'Content-Type': 'application/json'
                    }

            response = requests.request("POST", url, headers=headers, data=payload)
            data = response.json()
            data = data['data']
            # logger.info(f"got information from event api - \n{data}")
            event_details = 'Events - '
            if data !=[]:
                evnNum = 1
                for evn in data:
                    event_details = event_details+f"""{evnNum}. Event Title - {evn['title']}\nContent - {evn['content']}\nLink to Join Event - {evn['zoomLink']}\nStart Date - {evn['startDate']}\nEnd Date - {evn['endDate']}"""
            else:
                event_details = "No events available right now..."

        except:
            logger.error(f"Data from event api - \n{data}")
            event_details = 'No ongoing events.'
        # print("Events - ",event_details)
        asset_info = f"""**{all_asset_details['name']}**
                      Description - {all_asset_details['description']}
                      Asset's Location is {all_asset_details['location']}.
                      Asset is in {all_asset_details['currency']} Currency.
                      {status}
                      Visibility of asset is {visibility}.
                      Asset vertical type is {all_asset_details['assetVertical']}.
                      Trading mode is {all_asset_details['investmentMode']}.
                      IRR(Internal Rate of Return/Rate of Return) - {rateOfReturn}
                      {retirementEligible}
                      Impacts - {impacts}
                      {manager}
                      {company}
                      Latest Update are - 
                            {updates}
                      Investment Details - 
                            {investment_details}
                      Exit Strategy - {exitStrategy}
                      Key Highlights - 
                            {keyHighlights}                      
                      {event_details}
                      """
        # print(asset_info,all_asset_details['investmentMode'],asset_id)
        return asset_info,all_asset_details['investmentMode'],asset_id
    except Exception as e:
        logger.error(f"failed to get asset details - {str(e)}")
        return "Asset is not available at Marketplace", "Not available", None


def invest_page_trading_order_book_data(domain,asset_id,token):
    # BIDs 
    url = f"https://{domain}/investor/trade/{asset_id}/open/buy/offers"
    payload = {}
    headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
    response = requests.request("GET", url, headers=headers, data=payload)
    data = response.json() 
    BIDS = "BIDS from Order BOOK - \n"
    c = 0
    try:
        for d in data['data']:
            if c==4:
                break
            tempBid = f"Available Unit - {d['availableUnits']} at Price - {d['price']}"
            BIDS = BIDS +'\n'+ tempBid
            c=c+1
        BIDS = BIDS + '\n' + f"For more details on BIDs or Asks and Trading for this asset checkout - 'Invest' Tab for this asset. Or you can reach out to our support team support@evident.capital incase of any query."
    except:
        BIDS = "No data available on Bids at this moment."
    # print("BIDS no error")
    # Asks
    url = f"https://{domain}/investor/trade/{asset_id}/open/sell/offers"
    payload = {}
    headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
    response = requests.request("GET", url, headers=headers, data=payload)
    data = response.json() 
    ASKS = "Asks from Order Book - \n"
    c=0
    try:
        for d in data['data']:
            if c==4:
                break
            tempAsks = f"Available Unit - {d['availableUnits']} at Price - {d['price']}"
            ASKS = ASKS + '\n' + tempAsks
            c=c+1
        ASKS = ASKS + '\n' + f"For more details on Asks or Bids and Trading for this asset checkout - 'Invest' Tab for this asset. Or you can reach out to our support team support@evident.capital incase of any query."
    except:
        ASK = "No Data Available at this moment for 'ASKs'."
    # print("ASKS no error")
    # Holdings
    url = f"https://{domain}/investor/trade/{asset_id}/holdings"
    payload = {}
    headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
    response = requests.request("GET", url, headers=headers, data=payload)
    data = response.json()
    # print(data)
    try:
        if data['holding'] is not None:
            Units = float(data['holding']['units'])
            # print("Units - ", Units)
            Currency = data['holding']['asset']['currency']
            # print("Currency Units no error")
        else:
            Units = 0.0
            Currency = ""
    except:
        Units = 0.0
        Currency = ""
    url = f"https://{domain}/investor/trade/{asset_id}/tickers?range=iM"
    payload = {}
    headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
    response = requests.request("GET", url, headers=headers, data=payload)
    response = response.json()
    try:
        ltp = float(response['ltp']) if response['ltp'] is not None else 0
        Holdings = Currency +' ' + str(Units*ltp)
    except:
        Holdings = "No Holdings available"
    # print("Holdings no error")
    url = f"https://{domain}/investor/trade/{asset_id}/market-data"
    payload = {}
    headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
    response = requests.request("GET", url, headers=headers, data=payload)
    response = response.json()
    try:
        highest_bid = response['open_offers']['highestBid']['price'] if not None else 0
        lowest_ask = response['open_offers']['lowestAsk']['price'] if not None else 0
    except:
        highest_bid = 0
        lowest_ask = 0
    # print("no error in asks")
    return BIDS, ASKS, Holdings, highest_bid, lowest_ask


def invest_page_commitment_page_data(domain,asset_id,token):
    url = f"https://{domain}/investor/asset/{asset_id}/commitment-details"
    payload = {}
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json' 
    }
    response = requests.request('GET', url, headers=headers,data=payload)
    data = response.json()
    try:
        unit_price = data['ratio']
    except:
        unit_price = "Not available"
    try:
        target_amount = data['targetAmount']
        raised_amount = data['raisedAmount'] # this is also total committed amount shown in market commitments
        allocation_remaining = target_amount - raised_amount
    except:
        target_amount = "Not available"
        raised_amount = "Not available"
        allocation_remaining = "Not available"
    try:
        mini_amount = data['minimumAmount']
        max_amount = data['maximumAmount']
        myTotalCommitted = data['myTotalCommitted']
    except:
        mini_amount = "Not available"
        max_amount = "Not available"
        myTotalCommitted = "Not available"
    try:
        commit_id = data['id']
        url = f"https://{domain}/investor/commitment/{commit_id}/market-commitment?page=1"
        payload = {}
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json' 
        }
        response = requests.request('GET', url, headers=headers,data=payload)
        market_commitments = response.json()['data']

        # Market Commitments
        c = 0
        MarketCommitData = 'On going Market Commits are as follow - '
        for mc in market_commitments:
            if c==4:
                break
            date = mc['createdAt'].split('T')[0]
            time = mc['createdAt'].split('T')[1].split(".")[0]
            status = mc['status'][0]+mc['status'][1:].lower()
            commitmentAmount = mc['commitmentAmount']
            totalAmount = mc['totalAmount']
            temp_commits = f"On {date} at {time}, an {status} of {commitmentAmount} TPLT worth USD {totalAmount} was recorded."
            MarketCommitData = MarketCommitData + '\n' + temp_commits
            c+=1
        MarketCommitData = MarketCommitData +'\n\n'+ 'For more details about Market Commitments you can reach out to our support team at support@evident.capital'
    except:
        MarketCommitData = "Market Commits are unavailable right now."
    return MarketCommitData,unit_price,allocation_remaining,raised_amount,mini_amount,max_amount,myTotalCommitted


def invest_question_flow(token,domain,asset_name):
    all_asset_details,investment_mode,asset_id = get_specific_asset_details(asset_name,token,domain)
    # print(all_asset_details,investment_mode,asset_id)
    if all_asset_details == "Asset is not available at Marketplace":
        return all_asset_details, "Not available"

    prompt = ""
    if investment_mode.lower() == 'trading':
        # print("Asset is in trade")
        BIDS, ASKS, Holdings, highest_bid, lowest_ask = invest_page_trading_order_book_data(domain,asset_id,token)
        buy_now = f"Buy now: Select an open order from the order book, and define the amount of units you would like to buy.\nStep 1: Click on Asset in which you want to invest\nStep 2: Click on 'Invest' tab present at top-right\nStep 3: Scrolldown little bit and Click on 'Buy Now'\nStep 4: Select your preffered offer from 'Asks' section(By default 1st offer will be selected).\nStep 5: Add referal code if you have any else skip this step.\nStep 6: Add number of units you want to buy.\nStep 7: Click on 'I agree to the asset specific terms' checkbox, make sure you read all terms carefully if present.\nStep 8: Click on 'Buy Now'.\nIf you are unable to see 'Buy Now' option then check if you have sufficient balance. If not then click on add fund or register your bank account as available option and continue process."
        place_bid = f"Place Bid: Define a price and the amount of units you would like to buy, and place an open order on the order book.Step 1: Click on Asset in which you want to invest\nStep 2: Click on 'Invest' tab present at top-right\nStep 3: Scrolldown little bit and Click on 'Place Bid'\nStep 4: Enter Price per unit you want to place bid for.\nStep 5: Enter number of Unit you want to buy.\nStep 6: Click on 'I agree to the asset specific terms' checkbox, make sure you read all terms carefully if present.\nStep 7: Click on 'Place Bid'.\nIf you are unable to see 'Place Bid' option then check if you have sufficient balance, or bank account is not registed yet. If not then click on available option and continue process."
        sell_now = f"Sell now: Select an open order from the order book, and define the amount of units you would like to sell.\nStep 1: Click on Asset in which you want to invest\nStep 2: Click on 'Invest' tab present at top-right\nStep 3: Scrolldown little bit and Click on 'Sell Now'\nStep 4: Select your preffered offer from 'Bids' section(By default 1st offer will be selected).\nStep 5: Add referal code if you have any else skip this step.\nStep 6: Add number of units you want to sell.\nStep 7: Click on 'I agree to the asset specific terms' checkbox, make sure you read all terms carefully if present.\nStep 8: Click on 'Sell Now'.\nIf you are unable to proceed as 'Sell Now' option then check if you have sufficient Units for that asset or not. If not then you can not proceed further."
        place_ask = f"Place Ask: Define a price and the amount of units you would like to sell, and place an open order on the order book.\nStep 1: Click on Asset in which you want to invest\nStep 2: Click on 'Invest' tab present at top-right\nStep 3: Scrolldown little bit and Click on 'Place Ask'\nStep 4: Enter Price per unit you want.\nStep 5: Provide number of units you want to sell\nStep 6: Click on 'I agree to the asset specific terms' checkbox, make sure you read all terms carefully if present.\nStep 7: Click on 'Place Ask'.\nIf you are unable to proceed as 'Place Ask' option then check if you have sufficient Units for that asset or not. If not then you can not proceed further."
        
        prompt = f"""Understand user's question and based on following information provide most relevant answer to user's query. If you are unable to find answer from following information then revert politely that you do not have information for this question currently however our support team will be able to help you quickly with your query. Please feel free to reach out our team at support@evident.capital
                ## Bids for asset - 
                    {BIDS}

                ## Asks for asset - 
                    {ASKS}

                ## User's holdings for asset - {Holdings}
                ## Highest bid for asset - {highest_bid}
                ## Lowest ask for  asset - {lowest_ask}
                ## Asset Information - 
                    {all_asset_details}
                    
                ## To trade in this asset, following options are available, where to invest refer "Buy Now" and "Sell Now", and to sell refer "Place Bid" and "Place Ask" and provide detail information. -
                    1. "Buy Now" - Take an existing buy offer immediately.
                    {buy_now}

                    2. "Place Bid" - Make a buy offer (wait for seller to match).
                    {place_bid}

                    3. "Sell Now" - Take an existing sell offer immediately.
                    {sell_now}

                    4. "Place Ask" - Make a sell offer (wait for buyer to match).
                    {place_ask}
                """
        # response = get_gemini_response(question,prompt)

    # if asset is commitment
    elif investment_mode.lower() == 'commitment':
        print("Asset is in commitment")
        MarketCommitData,unit_price,allocation_remaining,raised_amount,mini_amount,max_amount,myTotalCommitted = invest_page_commitment_page_data(domain,asset_id,token)
        commit_flow = """You need to specify a Target Total Amount, which will be used to allocate units based on the price per unit. If your Available Balance is less than the Total to be Debited, you’ll need to either add the required amount or choose to Show Interest if you prefer not to add funds immediately. Otherwise, you can proceed directly by clicking Commit Now to confirm your commitment to the asset."""
        prompt = f"""Understand user's question and based on following information provide most relevant answer to user's query. If you are unable to find answer from following information then revert politely that you do not have information for this question currently however our support team will be able to help you quickly with your query. please feel free to reach out our team at support@evident.capital
                Unit Price for this asset to commit - {unit_price}
                Allocation Units Remaining - {allocation_remaining}
                Total Raised/Committed Amount based on Market - {raised_amount}
                Minimum Investment amount that you can do - {mini_amount}
                Maximum Investment amount that you can do - {max_amount}
                User's Total Committed amount for asset is - {myTotalCommitted}
                Market Commitment Details - 
                    {MarketCommitData}

                ## Asset Basic Overview Information - 
                    {all_asset_details}
                    
                How user can do commitment on this asset - {commit_flow}
                """
        # response = get_gemini_response(question,prompt)

    else:
        prompt = f"""Understand user's question and based on following information provide most relevant answer to user's query. If you are unable to find answer from following information then revert politely that you do not have information for this question currently however our support team will be able to help you quickly with your query. Please feel free to reach out our team at support@evident.capital
        Asset Basic Overview Information - 
                    {all_asset_details}
        """
    return prompt


def general_investment_guidelines(question):
    prompt = f"""User can invest in any asset based on Asset's investment mode. An Asset can be in Trading or in Commitment. Following are ways to invest in any Asset based on its investment mode.
    Provide below information to user to beign with investment.
    1. Trading - 
    Buy now: Select an open order from the order book, and define the amount of units you would like to buy.\nStep 1: Click on Asset in which you want to invest\nStep 2: Click on 'Invest' tab present at top-right\nStep 3: Scrolldown little bit and Click on 'Buy Now'\nStep 4: Select your preffered offer from 'Asks' section(By default 1st offer will be selected).\nStep 5: Add referal code if you have any else skip this step.\nStep 6: Add number of units you want to buy.\nStep 7: Click on 'I agree to the asset specific terms' checkbox, make sure you read all terms carefully if present.\nStep 8: Click on 'Buy Now'.\nIf you are unable to see 'Buy Now' option then check if you have sufficient balance. If not then click on add fund or register your bank account as available option and continue process."
    Place Bid: Define a price and the amount of units you would like to buy, and place an open order on the order book.Step 1: Click on Asset in which you want to invest\nStep 2: Click on 'Invest' tab present at top-right\nStep 3: Scrolldown little bit and Click on 'Place Bid'\nStep 4: Enter Price per unit you want to place bid for.\nStep 5: Enter number of Unit you want to buy.\nStep 6: Click on 'I agree to the asset specific terms' checkbox, make sure you read all terms carefully if present.\nStep 7: Click on 'Place Bid'.\nIf you are unable to see 'Place Bid' option then check if you have sufficient balance, or bank account is not registed yet. If not then click on available option and continue process."
    Sell now: Select an open order from the order book, and define the amount of units you would like to sell.\nStep 1: Click on Asset in which you want to invest\nStep 2: Click on 'Invest' tab present at top-right\nStep 3: Scrolldown little bit and Click on 'Sell Now'\nStep 4: Select your preffered offer from 'Bids' section(By default 1st offer will be selected).\nStep 5: Add referal code if you have any else skip this step.\nStep 6: Add number of units you want to sell.\nStep 7: Click on 'I agree to the asset specific terms' checkbox, make sure you read all terms carefully if present.\nStep 8: Click on 'Sell Now'.\nIf you are unable to proceed as 'Sell Now' option then check if you have sufficient Units for that asset or not. If not then you can not proceed further."
    Place Ask: Define a price and the amount of units you would like to sell, and place an open order on the order book.\nStep 1: Click on Asset in which you want to invest\nStep 2: Click on 'Invest' tab present at top-right\nStep 3: Scrolldown little bit and Click on 'Place Ask'\nStep 4: Enter Price per unit you want.\nStep 5: Provide number of units you want to sell\nStep 6: Click on 'I agree to the asset specific terms' checkbox, make sure you read all terms carefully if present.\nStep 7: Click on 'Place Ask'.\nIf you are unable to proceed as 'Place Ask' option then check if you have sufficient Units for that asset or not. If not then you can not proceed further."
    
    2. Commitment - You need to specify a Target Total Amount, which will be used to allocate units based on the price per unit. If your Available Balance is less than the Total to be Debited, you’ll need to either add the required amount or choose to Show Interest if you prefer not to add funds immediately. Otherwise, you can proceed directly by clicking Commit Now to confirm your commitment to the asset.
    """    

    response = get_gemini_response(question,prompt)

    return response


def deposit_fund(question):
    prompt = f"""
    
    """
    response = get_gemini_response(question,prompt)
    return response

