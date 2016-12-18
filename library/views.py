from django.shortcuts import render
from django.http import HttpResponseRedirect
from models import bookFromDict,commentsFromDict
from .DBmanager import *
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core.files.storage import FileSystemStorage
import time
from qsstats import QuerySetStats

database = DB()
#database.generate()

def main(request):
    database.latest = database.latest_books()
    popular_books = database.popular()
    return render(request, 'library/main.html', {'user': database.user, 'genres': database.genres,'books': database.latest,'booksp':popular_books})


def signin(request):
    return render(request, 'library/signin.html',{'user' : database.user, 'genres': database.genres})


def signup(request):
    return render(request, 'library/signup.html',{'user' : database.user, 'genres': database.genres})

def logout(request):
    database.user=None
    return render(request, 'library/main.html',{'user' : database.user, 'genres': database.genres,'books':database.latest})


def reg(request):
    if request.method == "POST":
        user=database.check_login(request.POST["login"])
        if user:
            database.user = None
            return render(request, 'library/signup.html',{'error_msg' : "This login is already used",'user':database.user, 'genres': database.genres})

        else:
            database.user = database.add_user(request.POST["name"],request.POST["surname"],request.POST["email"],request.POST["login"],request.POST["password"])
        return render(request, 'library/main.html',{'user' : database.user, 'genres': database.genres,'books':database.latest})



def check_user(request):
    if request.method == "POST":
        user=database.check_user(request.POST["email"],request.POST["password"])
        if user:
            database.user = database.dbmongo.user.find({'_id': ObjectId(user[0][0])})[0]
            return render(request, 'library/main.html', {'user': database.user, 'genres': database.genres,'books':database.latest})
        else:
            return render(request, 'library/signin.html', {'error_msg' : "Wrong login or password!",'user':database.user, 'genres': database.genres})


def admin(request):
    key = []
    if request.method == "POST":
        key.append(request.POST.get("genre"))
        if request.POST.get("author")==None:
            key.append("None")
        else: key.append(request.POST.get("author"))
        if request.POST.get("name")==None:
            key.append('')
        else: key.append(request.POST.get("name"))
        booksList = database.search(key)
        database.list = booksList
    elif request.GET.get('page'):
        booksList = database.list
    else:
        booksList = database.getBooksList()
        database.list=booksList

    paginator = Paginator(booksList, 25)  # Show per page
    page = request.GET.get('page')
    try:
        books = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        books = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        books = paginator.page(paginator.num_pages)

    return render(request, 'library/admin.html', {'books': books,'authors':database.authors,'genres':database.genres,})


def delete_book(request):
    if request.method == "POST":
        database.delete_book(request.POST["id"])
        return HttpResponseRedirect('/admin')


def add_book(request):

    if request.method == "POST":
        myfile = request.FILES['img']
        text = request.FILES['text']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        filename1 = fs.save(text.name, text)
        uploaded_file_url = fs.url(filename)
        text_url = fs.url(filename1)
        database.add_book(request.POST["name"],request.POST["author_id"],request.POST["genre"],request.POST["year"],request.POST["description"],uploaded_file_url,text_url)
        return HttpResponseRedirect('/admin')
    return render(request, 'library/add_book.html', {'authors': database.getAuthorsList(),'genres':database.getGenresList()})


def edit_book(request):
    if request.method == "POST":
        myfile = request.FILES['img']
        myfile1 = request.FILES['text']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        file = fs.save(myfile1.name, myfile1)
        uploaded_file_url = fs.url(filename)
        file_url = fs.url(file)
        database.update_book(request.POST["id"],request.POST["author_id"],request.POST["genre"],request.POST["name"],request.POST["year"],request.POST["description"],uploaded_file_url,file_url)
        admin(request)
        return HttpResponseRedirect('/admin')
    return render(request, 'library/edit_book.html', {'authors': database.getAuthorsList(),'genres':database.getGenresList(),'book':database.dbmongo.books.find({"_id":ObjectId(request.GET.get('id'))})[0]})


def dump(request):
    database.db_dump()
    return HttpResponseRedirect('/admin')


def restore(request):
    database.db_restore()
    return HttpResponseRedirect('/admin')

def statistics(request):
    if request.GET.get("day")=='1':
        data, date = database.statistic(3)
        data1,date1 = database.statistic2(3)
    elif request.GET.get("month")=='1':
        data, date = database.statistic(2)
        data1,date1 = database.statistic2(2)
    elif request.GET.get("year")=='1':
        data, date = database.statistic(1)
        data1,date1 = database.statistic2(1)
    else:
        data, date = database.statistic(2)
        data1,date1 = database.statistic2(2)
    return render(request, 'library/statistics.html',{'data':data,'date':date,'data1':data1,'date1':date1})



def search(request):
    key = []
    if request.method == "POST":
        key.append(request.POST.get("genre"))
        if request.POST.get("author")==None:
            key.append("None")
        else: key.append(request.POST.get("author"))
        if request.POST.get("name")==None:
            key.append('')
        else: key.append(request.POST.get("name"))
        booksList = database.search(key)
        database.list = booksList
    else:
        booksList = database.list

    paginator = Paginator(booksList, 20)  # Show per page
    page = request.GET.get('page')
    try:
        books = paginator.page(page)
    except PageNotAnInteger:
                # If page is not an integer, deliver first page.
        books = paginator.page(1)
    except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
        books = paginator.page(paginator.num_pages)

    return render(request, 'library/search.html', {'books': books,'authors':database.authors,'genres':database.genres,'user':database.user})


def book(request):
    if request.POST.get("deletecomment"):
        book = database.DeleteComment(request.POST["deletecomment"])
        comments = database.GetComments(book)
        book = database.dbmongo.books.find({'_id':ObjectId((book))})[0]
        book = bookFromDict(book)
        return render(request, 'library/book.html', {'book': book,'genres':database.genres,'user':database.user,'comments':comments})
    if request.POST.get("addcomment"):
        database.AddComment(request.POST["addcomment"],request.POST["comment"])
        comments = database.GetComments(request.POST['addcomment'])
        book = database.dbmongo.books.find({'_id':ObjectId((request.POST['addcomment']))})[0]
        book = bookFromDict(book)
        return render(request, 'library/book.html', {'book': book,'genres':database.genres,'user':database.user,'comments':comments})
    if request.POST.get("like"):
        if database.checkLike(request.POST['like'])==1:
            database.removeLike(request.POST['like'])
        else:
            database.addLike(request.POST['like'])
        comments = database.GetComments(request.POST['like'])
        book = database.dbmongo.books.find({'_id':ObjectId((request.POST['like']))})[0]
        book = bookFromDict(book)
        return render(request, 'library/book.html', {'book': book,'genres':database.genres,'user':database.user,'comments':comments})

    if request.POST.get("dislike"):
        if database.checkDislike(request.POST['dislike'])==1:
            database.removeDislike(request.POST['dislike'])
        else:
            database.addDislike(request.POST['dislike'])
        comments = database.GetComments(request.POST['dislike'])
        book = database.dbmongo.books.find({'_id':ObjectId((request.POST['dislike']))})[0]
        book = bookFromDict(book)
        return render(request, 'library/book.html', {'book': book,'genres':database.genres,'user':database.user,'comments':comments,})

    comments = database.GetComments(request.POST['book'])
    book = database.dbmongo.books.find({'_id':ObjectId((request.POST['book']))})[0]
    book = bookFromDict(book)
    return render(request, 'library/book.html', {'book': book,'genres':database.genres,'user':database.user,'comments':comments})


def top100(request):
    if request.GET.get("popularity")=='1':
        booksList = database.top100Popularity()
        database.list = booksList
        title = "Top 100 by popularity"
    elif request.GET.get("comments")=='1':
        booksList = database.top100Comments()
        database.list = booksList
        title = "Top 100 by comments"
    elif request.GET.get("date")=='1':
        booksList = database.top100Date()
        database.list = booksList
        title = "Top 100 by date"
    else:
        title = "None"
        booksList = database.list

    paginator = Paginator(booksList, 20)  # Show per page
    page = request.GET.get('page')
    try:
        books = paginator.page(page)
    except PageNotAnInteger:
                # If page is not an integer, deliver first page.
        books = paginator.page(1)
    except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
        books = paginator.page(paginator.num_pages)

    return render(request, 'library/top100.html', {'books': books,'authors':database.authors,'genres':database.genres,'user':database.user,'title':title})
