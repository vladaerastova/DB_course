from datetime import date
from pymongo import MongoClient
import MySQLdb
from models import bookFromDict,userFromDict,authorFromDict,commentsFromDict,genreFromDict
from bson.objectid import ObjectId
from bson.code import Code
from datetime import datetime
import redis
import random
import pickle
import subprocess
from bson.son import SON
import os
import shutil

class DB(object):
    def __init__(self):
        self.connection = MongoClient('localhost', 27017)
        self.r = redis.StrictRedis()
        self.dbmongo = self.connection.library
        self.dbmysql = MySQLdb.connect("127.0.0.1","root","12345","library")
        self.cursor = self.dbmysql.cursor()
        self.list = []
        self.user = None
        self.latest = self.latest_books()
        self.genres = self.getGenresList()
        self.authors = self.getAuthorsList()



    def check_user(self,login,password):
        sql = "select mongo_id from User where User.password = '%s' AND User.login = '%s' " %(password,login)
        self.cursor.execute(sql)
        self.dbmysql.commit()
        table = self.cursor.fetchall()
        return table

    def check_login(self,login):
        sql = "select mongo_id from User where User.login = '%s' " %(login)
        self.cursor.execute(sql)
        self.dbmysql.commit()
        table = self.cursor.fetchall()
        return table

    def add_user(self,name,surname,email,login,password):
        self.dbmongo.user.insert({"name":name,"surname":surname,"email":email})
        user = self.dbmongo.user.find({"email":email})
        sql = "insert into User (login,password,mongo_id)" \
          " values ('%s','%s','%s')" % (login,password,user[0]["_id"])
        self.cursor.execute(sql)
        self.dbmysql.commit()
        return user[0]

    def add_book(self,name,author,genre,year,description,img,text):
        keys = self.r.keys("*")
        for i in keys:
            if name in i or author in i or genre in i:
                self.r.delete(i)
        author = self.dbmongo.authors.find({"_id":ObjectId(author)})
        genre = self.dbmongo.genres.find({"_id":ObjectId(genre)})
        date = datetime.now()
        self.dbmongo.books.insert({"name":name,"author":author[0],"year":year,"date":date,"genre":genre[0],"description":description,"img":img,"likes":0,"dislikes":0,"text":text})


    def delete_book(self,number):
        book = self.dbmongo.books.find({"_id":ObjectId(number)})[0]
        keys = self.r.keys("*")
        for i in keys:
            if str(book["genre"]["_id"]) in i or str(book["author"]["_id"]) in i or book["name"] in i:
                self.r.delete(i)
        self.dbmongo.books.remove({"_id":ObjectId(number)})


    def update_book(self,number,author,genre,name,year,description,img,text):
        book = self.dbmongo.books.find({"_id":ObjectId(number)})[0]
        author1 = self.dbmongo.authors.find({"_id":ObjectId(author)})
        genre1 = self.dbmongo.genres.find({"_id":ObjectId(genre)})
        keys = self.r.keys("*")
        for i in keys:
            if author in i or genre in i or name in i or str(book["genre"]["_id"]) in i or str(book["author"]["_id"]) in i or book["name"] in i:
                self.r.delete(i)
        self.dbmongo.books.update(
            { "_id": ObjectId(number) },
            { "$set":
                {
                    "author": author1[0],
                    "genre": genre1[0],
                    "name": name,
                    "year": year,
                    "description":description,
                    "img":img,
                    "text":text
                }
            }
        )

    def generate(self):
        self.r.flushdb()
        '''for i in range (0,40000):
                rand_author = random.randint(0, 7)
                rand_genre =  random.randint(0, 18)
                author = self.dbmongo.authors.find().skip(rand_author).next()
                genre = self.dbmongo.genres.find().skip(rand_genre).next()
                year = random.randint(1500, 2016)
                name ="Book"
                img ="http://s5.goods.ozstatic.by/1000/938/15/1/1015938_0.jpg"
                likes = random.randint(0,500)
                dislikes = random.randint(0,500)
                description = "Interesting book about...."
                date = datetime.utcnow()
                text = "/media/Deich-Bradbury.pdf"
                book = {'author': author,'genre': genre, 'name': name,'year': year,'date': date,'img':img,'likes':likes,'dislikes':dislikes,'description':description,'text':text}
                self.dbmongo.books.insert(book)
        print "Done"'''
        for i in range(0,30000):
            rand_user = random.randint(0, 7)
            rand_book = random.randint(0, 39999)
            user = self.dbmongo.user.find().skip(rand_user).next()
            book = self.dbmongo.books.find().skip(rand_book).next()
            comment = "Generated comment"
            self.dbmongo.comment.insert({'user':user,'book':book,'comment':comment,'date':datetime.utcnow()})
        print "Done"

    def getBooksList(self):
        books = []
        book = self.dbmongo.books.find().sort(u'date',-1)
        for x in book:
            books.append(bookFromDict(x))
        return books

    def getAuthorsList(self):
        authors = []
        author = self.dbmongo.authors.find().sort(u'name',1)
        for x in author:
            authors.append(authorFromDict(x))
        return authors

    def getGenresList(self):
        authors = []
        author = self.dbmongo.genres.find().sort(u'name',1)
        for x in author:
            authors.append(genreFromDict(x))
        return authors

    def db_dump(self):
        cmd="mongodump  -db library"
        print subprocess.check_output(cmd,stderr=subprocess.STDOUT,shell=True)

    def db_restore(self):
        cmd="mongorestore -db library  dump/library"
        print subprocess.check_output(cmd,stderr=subprocess.STDOUT,shell=True)

    def latest_books(self):
        books = self.dbmongo.books.find().sort(u'date',-1)
        book=[]
        x=0
        for i in books:
            book.append(bookFromDict(i))
            x+=1
            if x==10:
                break
        return book

    def popular(self):
        books = self.dbmongo.books.find().sort(u'likes',-1).limit(10)
        book=[]
        x=0
        for i in books:
            book.append(bookFromDict(i))
            x+=1
            if x==10:
                break
        return book

# -------------------------------------Search Cache
    def search(self,key):
        print key
        if self.r.exists(key) != 0:
            book = pickle.loads(self.r.get(key))
            self.dbmongo.cachehit.insert({'date':datetime.utcnow()})
        else:
            if key[0] != 'None':
                print key
                if key[1] != 'None':
                    print key
                    if key[2] != '':
                        book = list(self.dbmongo.books.find({"genre._id":ObjectId(key[0]),'author._id':ObjectId(key[1]),'name':key[2]}))
                    else:
                        book = list(self.dbmongo.books.find({"genre._id":ObjectId(key[0]),"author._id":ObjectId(key[1])}))
                elif key[2]!='':
                    book = list(self.dbmongo.books.find({"genre._id":ObjectId(key[0]),"name":key[2]}))
                else:
                    print key
                    book = list(self.dbmongo.books.find({"genre._id":ObjectId(key[0])}))
            elif key[1]!='None':
                if key[2]!='':
                    book = list(self.dbmongo.books.find({"author._id":ObjectId(key[1]),"name":key[2]}))
                else:
                    book = list(self.dbmongo.books.find({"author._id":ObjectId(key[1])}))
            elif key[2]!='':
                book = list(self.dbmongo.books.find({"name":key[2]}))
            else:
                self.list=[]
                book=[]
        self.r.set(key,  pickle.dumps(book))
        self.dbmongo.activity.insert({'date':datetime.utcnow()})
        books = []
        for x in book:
            books.append(bookFromDict(x))
        return books

#---------------------------------------------------------
    def GetComments(self,book):
        books = []
        book = self.dbmongo.comment.find({'book._id':ObjectId(book)}).sort(u'date',-1)
        for x in book:
            books.append(commentsFromDict(x))
        return books

    def AddComment(self,book,comment):
        self.dbmongo.activity.insert({'date':datetime.utcnow()})
        book = self.dbmongo.books.find({"_id":ObjectId(book)})
        self.dbmongo.comment.insert({'user':self.user,'book':book[0],'comment':comment,'date':datetime.utcnow()})

    def DeleteComment(self,comment):
        self.dbmongo.activity.insert({'date':datetime.utcnow()})
        book = self.dbmongo.comment.find({"_id":ObjectId(comment)})[0]["book"]["_id"]
        self.dbmongo.comment.remove({"_id":ObjectId(comment)})
        return book


#---------------------------------------------------------------------------------------Likes

    def checkLike(self,book):
        like = self.dbmongo.likes.find({'book._id':ObjectId(book),'user':self.user}).count()
        return like

    def checkDislike(self,book):
        dislike = self.dbmongo.dislikes.find({'book._id':ObjectId(book),'user':self.user}).count()
        return dislike

    def addLike(self,book):
        self.dbmongo.activity.insert({'date':datetime.utcnow()})
        b = self.dbmongo.books.find({"_id":ObjectId(book)})
        self.dbmongo.likes.insert({'book':b[0],'user':self.user})
        self.dbmongo.books.update(
            { "_id": ObjectId(book) },
            { "$set":
                {
                    "likes": b[0]["likes"] + 1,
                }
            }
        )

    def addDislike(self,book):
        self.dbmongo.activity.insert({'date':datetime.utcnow()})
        b = self.dbmongo.books.find({"_id":ObjectId(book)})
        self.dbmongo.dislikes.insert({'book':b[0],'user':self.user})
        self.dbmongo.books.update(
            { "_id": ObjectId(book) },
            { "$set":
                {
                    "dislikes": b[0]["dislikes"] + 1,
                }
            }
        )
    def removeLike(self,book):
        self.dbmongo.activity.insert({'date':datetime.utcnow()})
        b = self.dbmongo.books.find({"_id":ObjectId(book)})
        self.dbmongo.likes.remove({'book._id':ObjectId(book),'user._id':ObjectId(self.user['_id'])})
        self.dbmongo.books.update(
            { "_id": ObjectId(book) },
            { "$set":
                {
                    "likes": b[0]["likes"] - 1,
                }
            }
        )

    def removeDislike(self,book):
        self.dbmongo.activity.insert({'date':datetime.utcnow()})
        b = self.dbmongo.books.find({"_id":ObjectId(book)})
        self.dbmongo.dislikes.remove({'book._id':ObjectId(book),'user._id':ObjectId(self.user['_id'])})
        self.dbmongo.books.update(
            { "_id": ObjectId(book) },
            { "$set":
                {
                    "dislikes": b[0]["dislikes"] - 1,
                }
            }
        )

    def top100Popularity(self):
        self.dbmongo.activity.insert({'date':datetime.utcnow()})
        books = self.dbmongo.books.aggregate([
        {"$sort": {"likes":-1}},
            {"$limit":100}])
        book=[]
        for i in books["result"]:
            book.append(bookFromDict(i))
        return book

    def top100Date(self):
        self.dbmongo.activity.insert({'date':datetime.utcnow()})
        books = self.dbmongo.books.aggregate([
        {"$sort": {"date":-1}},
            {"$limit":100}]);
        book=[]
        for i in books["result"]:
            book.append(bookFromDict(i))
        return book

    def top100Comments(self):
        self.dbmongo.activity.insert({'date':datetime.utcnow()})
        books = self.dbmongo.comment.aggregate([
        {"$group": {"_id": "$book._id","count": {"$sum": 1}}},
            {"$sort":{"count":-1}},
            {"$limit":100}])
        book=[]
        for i in books["result"]:
            book.append(bookFromDict(self.dbmongo.books.find({"_id":i["_id"]})[0]))
        return book

    def statistic(self,type):
        data = []
        date = []
        if type == 1:
            results = self.dbmongo.activity.aggregate(
               [{"$project":{"month": { "$month": "$date" },"year": { "$year": "$date" }}},
                {"$match":{"year":datetime.now().year }},
                {"$group":{"_id": {"month":"$month","year":"$year"},"count": {"$sum": 1}}},
                {"$sort":{"_id":1}}])
            for i in results["result"]:
                s=""
                s+=str(i["_id"]["year"])+"-"+str(i["_id"]["month"])
                date.append(s)
                data.append(str(int(i["count"])))
            return data,date
        if type == 2:
            results = self.dbmongo.activity.aggregate(
               [{"$project":{"month": { "$month": "$date" },"year": { "$year": "$date" },"day": { "$dayOfMonth": "$date" }}},
                {"$match":{"year":datetime.now().year }},
                {"$match":{"month":datetime.now().month }},
                {"$group":{"_id": {"month":"$month","year":"$year","day":"$day"},"count": {"$sum": 1}}},
                {"$sort":{"_id":1}}])
            for i in results["result"]:
                s=""
                s+=str(i["_id"]["year"])+"-"+str(i["_id"]["month"])+"-"+str(i["_id"]["day"])
                date.append(s)
                data.append(str(int(i["count"])))
            return data,date
        if type == 3:
            results = self.dbmongo.activity.aggregate(
               [{"$project":{"month": { "$month": "$date" },"year": { "$year": "$date" },"day": { "$dayOfMonth": "$date" },"hour":{"$hour":"$date"}}},
                {"$match":{"year":datetime.now().year }},
                {"$match":{"month":datetime.now().month }},
                {"$match":{"day":datetime.now().day }},
                {"$group":{"_id": {"month":"$month","year":"$year","day":"$day","hour":"$hour"},"count": {"$sum": 1}}},
                {"$sort":{"_id":1}}])
            for i in results["result"]:
                date.append(str(i["_id"]["hour"]))
                data.append(str(int(i["count"])))

        return data,date

    def statistic2(self,type):
        data = []
        date = []
        if type == 1:
            results = self.dbmongo.cachehit.aggregate(
               [{"$project":{"month": { "$month": "$date" },"year": { "$year": "$date" }}},
                {"$match":{"year":datetime.now().year }},
                {"$group":{"_id": {"month":"$month","year":"$year"},"count": {"$sum": 1}}},
                {"$sort":{"_id":1}}])
            for i in results["result"]:
                s=""
                s+=str(i["_id"]["year"])+"-"+str(i["_id"]["month"])
                date.append(s)
                data.append(str(int(i["count"])))
            return data,date
        if type == 2:
            results = self.dbmongo.cachehit.aggregate(
               [{"$project":{"month": { "$month": "$date" },"year": { "$year": "$date" },"day": { "$dayOfMonth": "$date" }}},
                {"$match":{"year":datetime.now().year }},
                {"$match":{"month":datetime.now().month }},
                {"$group":{"_id": {"month":"$month","year":"$year","day":"$day"},"count": {"$sum": 1}}},
                {"$sort":{"_id":1}}])
            for i in results["result"]:
                s=""
                s+=str(i["_id"]["year"])+"-"+str(i["_id"]["month"])+"-"+str(i["_id"]["day"])
                date.append(s)
                data.append(str(int(i["count"])))
            return data,date
        if type == 3:
            results = self.dbmongo.cachehit.aggregate(
               [{"$project":{"month": { "$month": "$date" },"year": { "$year": "$date" },"day": { "$dayOfMonth": "$date" },"hour":{"$hour":"$date"}}},
                {"$match":{"year":datetime.now().year }},
                {"$match":{"month":datetime.now().month }},
                {"$match":{"day":datetime.now().day }},
                {"$group":{"_id": {"month":"$month","year":"$year","day":"$day","hour":"$hour"},"count": {"$sum": 1}}},
                {"$sort":{"_id":1}}])
            for i in results["result"]:
                date.append(str(i["_id"]["hour"]))
                data.append(str(int(i["count"])))

        return data,date







