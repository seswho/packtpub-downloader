# -*- coding: utf-8 -*-
#!/usr/bin/python

from __future__ import print_function
import os
import sys
import glob
import math
import getopt
import requests
from tqdm import tqdm, trange
from config import BASE_URL, PRODUCTS_ENDPOINT, URL_BOOK_TYPES_ENDPOINT, URL_BOOK_ENDPOINT
from user import User
import time

# for current func name, specify 0 or no argument.
# for name of caller of current func, specify 1.
# for name of caller of caller of current func, specify 2. etc.
currentFuncName = lambda n=0: sys._getframe(n + 1).f_code.co_name


def display_http_error(myFunc, myErr, myStatus_Code):
    print('\nERROR (please copy and paste in the issue)')
    print(myFunc)
    print(myErr)
    print(myStatus_Code)
    
def book_request(user, offset, limit, verbose=False):
    data = []
    url = BASE_URL + PRODUCTS_ENDPOINT.format(offset=offset, limit=limit)
    if verbose:
        print(url)
    r = requests.get(url, headers=user.get_header())
    data += r.json().get('data', [])
    #print("in book_request data: {}\n\n".format(data))

    return url, r, data

def get_owned_books(user, offset=0, limit=25, is_verbose=False, is_quiet=False):
    '''
        Request all your books, return json with info of all your books
        Params
        ...
        header : str
        offset : int
        limit : int
            how many book wanna get by request
    '''
    # TODO: given x time jwt expired and should refresh the header, user.refresh_header()
    
    url, r, data = book_request(user, offset, limit, is_verbose)
    
    print("Getting list of books...")
    print(f'You have ~{str(r.json()["count"])} books, which may include duplicates')
    
    if not is_quiet:
        pages_list = trange(r.json()['count'] // limit, unit='Pages')
    else:
        pages_list = range(r.json()['count'] // limit)
    for i in pages_list:
        offset += limit
        data += book_request(user, offset, limit, is_verbose)[2]
    return data

def get_book_file_types(user, book_id):
    '''
        Return a list with file types of a book
    '''
    url = BASE_URL + URL_BOOK_TYPES_ENDPOINT.format(book_id=book_id)
    r = requests.get(url, headers=user.get_header())

    if  (r.status_code == 200): # success
        return r.json()['data'][0].get('fileTypes', [])
    elif (r.status_code == 401): # jwt expired 
        print("get_book_file_types")
        user.refresh_header() # refresh token 
        #get_book_file_types(user, book_id, format)  # call recursive
        get_book_file_types(user, book_id)  # call recursive
    elif (r.status_code == 404): # the book doesn't have the requested format
        #print("{} doesn't have any file types".format(book_id))
        # this product doesn't have any book formats listed it could be a video
        # just return an empty dictionary of file types
        return []
    else:
        display_http_error(currentFuncName() + ' --- ' + book_id, r.json(), r.status_code)
        return []

def get_book_url(user, book_id, format='pdf'):
    '''
        Return url of the book to download
    '''
    url = BASE_URL + URL_BOOK_ENDPOINT.format(book_id=book_id, format=format)
    r = requests.get(url, headers=user.get_header())

    if r.status_code == 200: # success
        return r.json().get('data', '')
    elif r.status_code == 401: # jwt expired 
        print("get_url_book")
        user.refresh_header() # refresh token 
        get_book_url(user, book_id, format)  # call recursive 
    else:
        display_http_error(currentFuncName() + ' --- ' + book_id, r.json(), r.status_code)
        return ''
    
def download_book(filename, url):
    '''
        Download your book
    '''
    print('Starting to download ' + filename)

    with open(filename, 'wb') as f:
        r = requests.get(url, stream=True)
        total = r.headers.get('content-length')
        if total is None:
            f.write(r.content)
        else:
            total = int(total)
            # TODO: read more about tqdm
            for chunk in tqdm(r.iter_content(chunk_size=1024), total=math.ceil(total//1024), unit='KB', unit_scale=True):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()
            print('Finished ' + filename)

def make_zip(filename):
    if filename[-4:] == 'code':
        os.replace(filename, filename[:-4] + 'zip')
    elif filename[-5:] == 'video':
        os.replace(filename, filename[:-5] + 'zip')

def move_current_files(root, book):
    sub_dir = f'{root}/{book}'
    does_dir_exist(sub_dir)
    for f in glob.iglob(sub_dir + '.*'):
        try:
            os.rename(f, f'{sub_dir}/{book}' + f[f.index('.'):])
        except OSError:
            os.rename(f, f'{sub_dir}/{book}' + '_1' + f[f.index('.'):])
        except ValueError as e:
            print(e)
            print('Skipping')

def does_dir_exist(directory):
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
        except Exception as e:
            print(e)
            sys.exit(2)

def main(argv):
    # thanks to https://github.com/ozzieperez/packtpub-library-downloader/blob/master/downloader.py
    email = None
    password = None
    root_directory = 'media' 
    book_file_types = ['pdf', 'mobi', 'epub', 'code', 'video']
    separate = None
    verbose = None
    quiet = None
    errorMessage = 'Usage: main.py -e <email> -p <password> [-d <directory> -b <book file types>|all -s -v -q]'
    ts1 = 0
    ts2 = 0

    # get the command line arguments/options
    try:
        opts, args = getopt.getopt(
            argv, 'e:p:d:b:svq', ['email=', 'pass=', 'directory=', 'books=', 'separate', 'verbose', 'quiet'])
    except getopt.GetoptError:
        print(errorMessage)
        sys.exit(2)

    # hold the values of the command line options
    for opt, arg in opts:
        if opt in ('-e', '--email'):
            email = arg
        elif opt in ('-p', '--pass'):
            password = arg
        elif opt in ('-d', '--directory'):
            root_directory = os.path.expanduser(
                arg) if '~' in arg else os.path.abspath(arg)
        elif opt in ('-b', '--books'):
            if arg == 'all':
                book_file_types = ['pdf', 'mobi', 'epub', 'code', 'video']
            else:
                book_file_types = arg.split(',')
        elif opt in ('-s', '--separate'):
            separate = True
        elif opt in ('-v', '--verbose'):
            verbose = True
        elif opt in ('-q', '--quiet'):
            quiet = True

    if verbose and quiet:
        print("Verbose and quiet cannot be used together.")
        sys.exit(2)

    # do we have the minimum required info?
    if not email or not password:
        print(errorMessage)
        sys.exit(2)

    # check if not exists dir and create
    does_dir_exist(root_directory)

    # create user with his properly header
    user = User(email, password)
    
    # once we login to the API and get the out jwt
    # testing has shown there is a ~15 minute life of the jwt
    # set a variable with the starting time stamp to check at a later
    # point to see if we're close to the 15 minute point and refresh
    # the jwt
    ts1 = time.time() # in seconds

    # get all your books
    books = get_owned_books(user, is_verbose=verbose, is_quiet=quiet)

    # remove any duplicate book records
    new_books = []
    seen = set()
    for book in books:
        prodid = book['productId']
        if prodid not in seen:
            seen.add(prodid)
            new_books.append(book)
    del seen
    print("Number of books owned after removing duplicates: {}".format(len(new_books)))

    if not quiet:
        books_iter = tqdm(new_books, unit='Book')
    else:
        books_iter = new_books
    ts1 = time.time()
    for book in books_iter:
        ts2 = time.time()
        if ((ts2 - ts1)/60) > 14:
            user = User(email, password) # just to make sure the jwt has not timed out, get a new one
            ts1 = ts2
        file_types = get_book_file_types(user, book['productId']) # get the different file type of current book
        for file_type in file_types:
            if file_type in book_file_types: #check to see if the file type(s) entered are available for the current book
                book_name = book['productName'].replace('  ',' ').replace(':', '-').replace('/','-').replace('Edition)','Edition')
                book_name = book_name.replace(', Second',' - Second').replace('-Second','- Second').replace('(Second',' - Second').replace('Hands - On','Hands-On')
                book_name = book_name.replace('7-','7 -').replace('  -',' -').strip()
                if separate: # are we putting the books into separate folders or all in one folder
                    filename = f'{root_directory}/{book_name}/{book_name}.{file_type}'
                    move_current_files(root_directory, book_name)
                else:
                    filename = f'{root_directory}/{book_name}.{file_type}'
                # get url of the book to download
                url = get_book_url(user, book['productId'], file_type) # get url of the book to download
                '''
                    some videos could have code along with the video
                    check to see if the current filename has 'code' as a file type
                    and replace the workd Video in the book name to Code to show
                    the difference between the two files since both are really .zip files
                '''
                if file_type == 'code' and 'Video]' in filename:
                    filename = filename.replace('Video].', 'Code].')
                if not os.path.exists(filename) and not os.path.exists(filename.replace('.code', '.zip')) and not os.path.exists(filename.replace('.video', '.zip')):
                    download_book(filename, url)
                    make_zip(filename)
                else:
                    if verbose:
                        tqdm.write(f'{filename} already exists, skipping.')

if __name__ == '__main__':
    main(sys.argv[1:])
