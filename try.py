import numpy as np
import pandas as pd
import tweepy
import json
from tweepy import OAuthHandler
from textblob import TextBlob
import matplotlib.pyplot as plt
import re
import xlwt
from django.utils.encoding import smart_str
from django.http import HttpResponse
import nltk 
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize, sent_tokenize

API_KEY = 'jewhefZEorHMnQN4HvqvrYpL2'
API_KEY_SECRET = 'qbabJv0ynqgKR7p5geeevls8SmewDWiD6DyJGXrLgnKKa2CGnv'
BEARER_TOKEN = 'AAAAAAAAAAAAAAAAAAAAABerUQEAAAAAAhgGpfpMR45s%2BX%2BO5rXe%2B7j28Ts%3DGhMEIAXCaJdWhE1aY8tdRYZVwpuSE6MnKLdS8halkIEx2gFxJL'
ACCESS_TOKEN = '1442913758108549121-lCcJQvEDsd11RY8JsWgJOgrDlMPlO3'
ACCESS_TOKEN_SECRET = 'xuemEYbUfBOBSY6PGlcR0PUg8689gzLVUDo2elVsP5AUF'
api2 = tweepy.Client(bearer_token= BEARER_TOKEN)
auth = tweepy.OAuthHandler( API_KEY , API_KEY_SECRET )
auth.set_access_token( ACCESS_TOKEN , ACCESS_TOKEN_SECRET )
api1 = tweepy.API(auth)

df = pd.DataFrame(columns = ['Tweets' , 'User' , 'User_statuses_count' , 
                            'user_followers' , 'User_location' , 'User_verified' ,
                            'fav_count' , 'rt_count' , 'tweet_date'] )

i = 0
for tweet in tweepy.Cursor(api1.search_tweets, q='covid', count=100, lang='en').items(20):
    print(i, end='\r')
    df.loc[i, 'Tweets'] = tweet.text
    df.loc[i, 'User'] = tweet.user.name
    df.loc[i, 'User_statuses_count'] = tweet.user.statuses_count
    df.loc[i, 'user_followers'] = tweet.user.followers_count
    df.loc[i, 'User_location'] = tweet.user.location
    df.loc[i, 'User_verified'] = tweet.user.verified
    df.loc[i, 'fav_count'] = tweet.favorite_count
    df.loc[i, 'rt_count'] = tweet.retweet_count
    df.loc[i, 'tweet_date'] = pd.to_datetime(tweet.created_at).date().strftime('%Y-%m-%d')
    i = i+1
    if i == 1000:
        break
    else:
        pass

    s=''
    l=[]
            #df['tweet_date'] = df['tweet_date'].apply(lambda x : x.strftime('%Y-%m-%d'))
    print(df['Tweets'])
    for a in df['Tweets']:
        s=s+a+'. '
        l.append(a)
print(len(s))
print(l)



def extractor(text):
    
    print('PROPER NOUNS EXTRACTED :')
    
    sentences = nltk.sent_tokenize(text)
    for sentence in sentences:
        words = nltk.word_tokenize(sentence)
        words = [word for word in words if word not in set(stopwords.words('english'))]
        tagged = nltk.pos_tag(words)
        for (word, tag) in tagged:
            if tag == 'NNP': # If the word is a proper noun
                print(word)

for z in l:
    clean=' '.join(re.sub('(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)', ' ',z).split())
    print(clean)
    print(extractor(clean))