from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

import numpy as np
import pandas as pd
import tweepy
import json
from tweepy import OAuthHandler
from textblob import TextBlob
import re
import xlwt
from django.utils.encoding import smart_str
from django.http import HttpResponse
from django.conf import settings

API_KEY = settings.API_KEY
API_KEY_SECRET = settings.API_KEY_SECRET
BEARER_TOKEN = settings.BEARER_TOKEN
ACCESS_TOKEN = settings.ACCESS_TOKEN
ACCESS_TOKEN_SECRET = settings.ACCESS_TOKEN_SECRET
NO_OF_TERMS = settings.NO_OF_TERMS



query = "covid"

auth = tweepy.OAuthHandler( API_KEY , API_KEY_SECRET )
auth.set_access_token( ACCESS_TOKEN , ACCESS_TOKEN_SECRET )
api1 = tweepy.API(auth)

api2 = tweepy.Client(bearer_token= BEARER_TOKEN)

def home(request):
    return render(request,'home.html')

def hashtagForm(request):
    return render(request,"hashtagForm.html")

def tweetCount(request):
    tweetCount = api2.get_recent_tweets_count(query)
    tweetData = []
    for tweet in tweetCount.data:
        obj = {}
        obj['end'] = tweet['end']
        obj['count'] = tweet['tweet_count']
        tweetData.append(obj)
    tweetData = json.dumps(tweetData)
    return render(request, 'tweetCount.html', {'tweetData' : tweetData})


def targetedAds(request):
    TWEET =  1266735261012111360
    users = api2.get_liking_users(TWEET)
    return render(request,'targetedAds.html', {'users' : users})

def stream(data, file_name):
        df = pd.DataFrame(columns = ['Tweets' , 'User_name','User_id' , 'User_statuses_count' , 
                            'user_followers' , 'User_location' , 'User_verified' ,
                            'fav_count' , 'rt_count', 'tweet_date','url'] )

        i = 0
        # status_count - Total tweets by user
        # for tweet in tweepy.Cursor(api1.search_tweets, q=data, count=50, lang='en', result_type="popular").items(NO_OF_TERMS):
        for tweet in api1.search_tweets(q=data,count=50,lang='en', result_type="popular"):
            print(i, end='\r')
            df.loc[i, 'Tweets'] = tweet.text
            df.loc[i, 'User_name'] = tweet.user.name
            df.loc[i, 'User_id'] = tweet.user.screen_name
            df.loc[i, 'User_statuses_count'] = tweet.user.statuses_count
            df.loc[i, 'user_followers'] = tweet.user.followers_count
            df.loc[i, 'User_location'] = tweet.user.location
            df.loc[i, 'User_verified'] = tweet.user.verified
            df.loc[i, 'fav_count'] = tweet.favorite_count
            df.loc[i, 'rt_count'] = tweet.retweet_count
            df.loc[i, 'tweet_date'] = pd.to_datetime(tweet.created_at).date().strftime('%Y-%m-%d')
            if not len(tweet.entities['urls']) :
                df.loc[i, 'url'] = "not-available"
            else:
                df.loc[i, 'url'] = tweet.entities['urls'][0]['url']
            i = i+1
            if i == 1000:
                break
            else:
                pass
       
        return df

def sentimentAnalysis(request):
    polarity = 0
    positive = 0
    wpositive = 0
    spositive = 0
    negative = 0
    wnegative = 0
    snegative = 0
    neutral = 0
    
    
#Clean tweet
    def clean_tweet(tweet):
        return ' '.join(re.sub('(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)', ' ', tweet).split())

#sentiment analysis
    def analyze_sentiment(tweet):
        analysis = TextBlob(tweet)
        nonlocal polarity
        polarity += analysis.sentiment.polarity
        if(analysis.sentiment.polarity > 0 and analysis.sentiment.polarity <= 0.3):
            nonlocal wpositive
            wpositive += 1
            return 'weakly positive'
        elif(analysis.sentiment.polarity > 0.3 and analysis.sentiment.polarity <= 0.6):
            nonlocal positive
            positive +=1
            return 'positive'
        elif (analysis.sentiment.polarity > 0.6 and analysis.sentiment.polarity <= 1):
            nonlocal spositive
            spositive +=1
            return 'strongly positive'
        elif (analysis.sentiment.polarity > -0.3 and analysis.sentiment.polarity <= 0):
            nonlocal wnegative
            wnegative +=1
            return 'weakly negative'
        elif (analysis.sentiment.polarity > -0.6 and analysis.sentiment.polarity <= -0.3):
            nonlocal negative
            negative +=1
            return 'negative'
        elif (analysis.sentiment.polarity > -1 and analysis.sentiment.polarity <= -0.6):
            nonlocal snegative
            snegative +=1
            return 'strongly negative'
        elif(analysis.sentiment.polarity == 0):
            nonlocal neutral
            neutral +=1
            return 'neutral'


#percentage calculation
    def percentage(part, whole):
            temp = 100 * float(part) / float(whole)
            return format(temp, '.2f') 
    df=stream(data=query, file_name='my_tweets')
    print(df.head())
    df['clean_tweet'] = df['Tweets'].apply(lambda x : clean_tweet(x))
    df['Sentiment'] = df['clean_tweet'].apply(lambda x : analyze_sentiment(x) )
    print(df.tail())
    print(positive)
    #total positive,neutral and negative
    tp=positive+wpositive+spositive
    tn=negative+wnegative+snegative
    n=neutral
    print("Total positive " + str(tp))
    print("Total Negative " + str(tn))
    print("Total Neutral " + str(n))

    data = {"totalPositive" : tp,"totalNegative" : tn, "totalNeutral": n, "positive" : positive , "wpositive" : wpositive,"spositive" : spositive,"negative": negative, "wnegative": wnegative, "snegative" : snegative , "neutral" : neutral}
    datalist = [positive,wpositive,spositive,negative,wnegative,snegative,neutral]
    
    return render(request,'sentimentAnalysis.html',{'data':data, 'datalist' : datalist})

Filedata = []
def hashtagAnalysis(request):
    df=stream(data=query, file_name='my_tweets')
    # df.to_excel('{}.xlsx'.format('my_tweets'))
    json_records = df.reset_index().to_json(orient ='records',date_format="iso")
    data = []
    data = json.loads(json_records)
    print(data)
    global Filedata
    Filedata = data
    return render(request,'hashtagAnalysis.html',{'d': data})

def downloadFile(request):
    # content-type of response
    response = HttpResponse(content_type='application/ms-excel')

    #decide file name
    response['Content-Disposition'] = 'attachment; filename= ' + query + ".xls"

    #creating workbook
    wb = xlwt.Workbook(encoding='utf-8')

    #adding sheet
    ws = wb.add_sheet("sheet1")

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    # headers are bold
    font_style.font.bold = True

    #column header names, you can use your own headers here
    columns = ["Tweets","User_name","User_id","User_statuses_count","User_location","user_followers","user_verified","fav_count","rt_count","tweet_date","url" ]

    #write column headers in sheet
    for col_num in range(len(columns)):
      ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    
    for my_row in Filedata:
      row_num = row_num + 1
      print(my_row)
      ws.write(row_num, 0, my_row['Tweets'], font_style)
      ws.write(row_num, 1, my_row['User_name'], font_style)
      ws.write(row_num, 1, my_row['User_id'], font_style)
      ws.write(row_num, 2, my_row['User_statuses_count'], font_style)
      ws.write(row_num, 3, my_row['User_location'], font_style)
      ws.write(row_num, 4,my_row['user_followers'], font_style)
      ws.write(row_num, 5,my_row['User_verified'], font_style)
      ws.write(row_num, 6,my_row['fav_count'], font_style)
      ws.write(row_num, 7,my_row['rt_count'], font_style)
      ws.write(row_num, 8,my_row['tweet_date'], font_style)
      ws.write(row_num,9,my_row['url'], font_style)

    wb.save(response)
    return response
    


# def interestAnalysis(request):
#     user = "@Dhiyanesh01"
#     favList = []
#     fav = {}
#     for favorite in tweepy.Cursor(api1.get_favorites,id=user ).items(100):
#         fav['authorScreenname'] = str(favorite.user.screen_name.encode("utf-8"))
#         fav['authorName'] = str(favorite.user.name.encode("utf-8"))
#         fav['tweetId'] = str(favorite.id)
#         fav['tweetText'] = str(favorite.text.encode("utf-8"))
#         favList.append(fav)
#         print(favorite)
#     print(favList)
#     return render(request,'interestAnalysis.html',{'favourite': favList} )

def interestAnalysis(request):
    user = "@Dhiyanesh01"
    favList = []
    for favorite in tweepy.Cursor(api1.get_favorites,id=user ).items(100):
        fav = {}
        fav['authorScreenname'] = str(favorite.user.screen_name)
        fav['authorName'] = str(favorite.user.name)
        fav['tweetId'] = str(favorite.id)
        fav['tweetText'] = str(favorite.text)
        favList.append(fav)
        print(favorite)
    print(favList)
    return render(request,'interestAnalysis.html',{'favourite': favList} )
    