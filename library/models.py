from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Author:
    def __init__(self, _id, name):
        self.Id = _id
        self.Name = name



def authorFromDict(dict):
    author = Author(dict['_id'], dict['name'])
    return author

class Genre:
    def __init__(self, _id, name):
        self.Id = _id
        self.Name = name



def genreFromDict(dict):
    genre = Genre(dict['_id'], dict['name'])
    return genre

class Book:
    def __init__(self, _id, author, name,year,date,genre,likes,img,description,dislikes,text):
        self.Id = _id
        self.Author = author
        self.Name = name
        self.Year = year
        self.Date = date
        self.Genre = genre
        self.Likes = likes
        self.Img = img
        self.Description = description
        self.Dislikes = dislikes
        self.Text = text
      #  self.Comments = comments


def bookFromDict(dict):
    book = None
    if dict != None:
        book = Book(dict['_id'], authorFromDict(dict['author']), dict['name'],
                              dict['year'], dict['date'],genreFromDict(dict['genre']),dict['likes'],dict['img'],dict['description'],dict['dislikes'],dict['text'])
    return book

class User:
    def __init__(self, _id, name,surname,email):
        self.Id = _id
        self.Name = name
        self.Surname = surname
        self.Email = email

def userFromDict(dict):
    user = User(dict['_id'], dict['name'],dict['surname'],dict['email'])
    return user

class Comment:
    def __init__(self, _id,book, user,comment,date):
        self.Id = _id
        self.Book = book
        self.User = user
        self.Comment = comment
        self.Date = date

def commentsFromDict(dict):
    comments = Comment(dict['_id'],bookFromDict(dict['book']),userFromDict(dict['user']),dict['comment'],dict['date'])
    return comments
