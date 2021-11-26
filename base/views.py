from django.shortcuts import redirect, render
from django.http import HttpResponse
import numpy as np
import pandas as pd
from collections import Counter
from collections import OrderedDict
import tweepy
import json
from tweepy import OAuthHandler
from textblob import TextBlob
import re
import xlwt
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from django.utils.encoding import smart_str
from django.http import HttpResponse
from django.conf import settings

#Retrieve Keys and Tokens from .env
API_KEY = settings.API_KEY
API_KEY_SECRET = settings.API_KEY_SECRET
BEARER_TOKEN = settings.BEARER_TOKEN
ACCESS_TOKEN = settings.ACCESS_TOKEN
ACCESS_TOKEN_SECRET = settings.ACCESS_TOKEN_SECRET
NO_OF_TERMS = settings.NO_OF_TERMS

# Authentication
auth = tweepy.OAuthHandler( API_KEY , API_KEY_SECRET )
auth.set_access_token( ACCESS_TOKEN , ACCESS_TOKEN_SECRET )
api1 = tweepy.API(auth)
api2 = tweepy.Client(bearer_token= BEARER_TOKEN)

#Global Variables
Filedata = []


def home(request):
    return render(request,'home.html')


#All Tweet Analysis based on Hashtag

def tweetAnalysis(request):
    if request.method == 'POST':
        query = request.POST['hashtag']
        request.session['hashtagQuery'] = query
    elif 'hashtagQuery' in request.session and request.method  == 'GET':
        query = request.session['hashtagQuery']
        print(query)
    else:
        return redirect('/')
    tweetCountData = tweetCount(query)
    tweetData = hashtagAnalysis(query)
    sentimentData = sentimentAnalysis(query)
    return render(request,'tweetAnalysis.html',{"tweetCountData" :tweetCountData,"tweetData":tweetData,"sentimentData":sentimentData })

#Tweet count
def tweetCount(query):
    tweetCount = api2.get_recent_tweets_count(query)
    tweetCountData = []
    for tweet in tweetCount.data:
        obj = {}
        obj['end'] = tweet['end']
        obj['count'] = tweet['tweet_count']
        tweetCountData.append(obj)
    tweetCountData = json.dumps(tweetCountData)
    return tweetCountData

#Create Dataframe with api response on serach tweets 
def stream(data):
        df = pd.DataFrame(columns = ['Tweets' , 'User_name','User_id' , 'User_statuses_count' , 
                            'user_followers' , 'User_location' , 'User_verified' ,
                            'fav_count' , 'rt_count', 'tweet_date','url'] )

        i = 0
        # status_count - Total tweets by user
        for tweet in api1.search_tweets(q=data,count=50,lang='en', result_type="popular"):
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

#Hashtag Analysis
def hashtagAnalysis(query):
    df=stream(query)
    json_records = df.reset_index().to_json(orient ='records',date_format="iso")
    tweetData = []
    tweetData = json.loads(json_records)
    global Filedata
    Filedata = tweetData
    return tweetData

#Sentiment Analysis
def sentimentAnalysis(query):
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

    #Find sentiment 
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

    df=stream(query)
    df['clean_tweet'] = df['Tweets'].apply(lambda x : clean_tweet(x))
    df['Sentiment'] = df['clean_tweet'].apply(lambda x : analyze_sentiment(x) )

    #total positive,neutral and negative
    tp=positive+wpositive+spositive
    tn=negative+wnegative+snegative
    n=neutral

    #create object for pie-chart
    data = {"totalPositive" : tp,"totalNegative" : tn, "totalNeutral": n, "positive" : positive , "wpositive" : wpositive,"spositive" : spositive,"negative": negative, "wnegative": wnegative, "snegative" : snegative , "neutral" : neutral}
    datalist = [positive,wpositive,spositive,negative,wnegative,snegative,neutral]

    #convert to percentage 
    percentageDatalist = []
    total = sum(datalist)
    if total != 0:
        for entry  in datalist:
            f=(entry/total)*100
            percentageDatalist.append(f)
    dataObj ={"data": data,"datalist":percentageDatalist}
    return dataObj

#Handles Excel sheet download 
def downloadFile(request):

    query = request.session['hashtagQuery']

    # content-type of response
    response = HttpResponse(content_type='application/ms-excel')

    #decide file name
    response['Content-Disposition'] = 'attachment; filename= ' + query + ".xls"

    #creating workbook
    wb = xlwt.Workbook(encoding='utf-8')

    #adding sheet
    ws = wb.add_sheet("sheet1",cell_overwrite_ok=True)

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

    print(Filedata)
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


    
def interestAnalysis(request):
    if request.method == "POST":
        user = request.POST['username']
        tweets=[]
        s=''
        def extractor(text):
            ans=[]
            sentences = nltk.sent_tokenize(text)
            for sentence in sentences:
                words = nltk.word_tokenize(sentence)
                words = [word for word in words if word not in set(stopwords.words('english'))]
                tagged = nltk.pos_tag(words)
                for (word, tag) in tagged:
                    if tag == 'NNP':
                        ans.append(word)
            return ans

        for favorite in tweepy.Cursor(api1.get_favorites,id=user ).items(100):
            tweet=str(favorite.text)
            tweets.append(tweet)
            neat=' '.join(re.sub('(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)', ' ',tweet).split())
            s=s+neat+'. '

        
        datalist=extractor(s)
        datalist = list(filter(('RT').__ne__, datalist))
        datalist = [i for i in datalist if len(i)!=1 ]
        datalist = [i for i in datalist  if len(i)!=2 ]
        datalist = [i for i in datalist if len(i)!=3 ]
        return render(request,'interestAnalysis.html',{'favourite': datalist} )
    else:
        return render(request,'interestAnalysis.html')


def targetedAds(request):
    TWEET =  1266735261012111360
    if request.method == 'POST':
        USERNAME = ''
        targetUserCount = 30
        USERNAME = request.POST['username']
        #single tweet
        users = api2.get_liking_users(TWEET)

        #Last ten tweets from a user
        res = api2.get_user(username=USERNAME)
        if(res.data == None):
            error = res.errors[0]['detail']
            return render(request,"targetedAds.html", {'error' : error })
        userId = res.data["id"]
        
        tweets = api2.get_users_tweets(userId)
        targetUsers = []
        sortedTargetUsers = []
        for tweet in tweets.data:
            tweetId = tweet["id"]
            #Recent most 100 liked users
            usersData = api2.get_liking_users(tweetId).data
            if usersData != None :
                for user in usersData:
                    targetUsers.append(user.username)
        targetUsers = [item for items, c in Counter(targetUsers).most_common() for item in [items] * c]
        sortedTargetUsers = list(OrderedDict.fromkeys(targetUsers))
        if len(sortedTargetUsers) > 30:
            sortedTargetUsers = sortedTargetUsers[0: targetUserCount]
        print(sortedTargetUsers)
        return render(request,'targetedAds.html', {'users' : users,'targetUsers':sortedTargetUsers })
    else:
        return render(request,'targetedAds.html')
