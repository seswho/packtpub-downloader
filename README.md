# PacktPub Downloader

Script to download all your PacktPub books inspired by https://github.com/ozzieperez/packtpub-library-downloader and https://github.com/lmbringas/packtpub-downloader

## Usage:
    pip install -r requirements.txt
	python main.py -e <email> -p <password> [-d <directory> -b <book file types> -s -v -q]

##### Example: Download books in PDF format
	python main.py -e hello@world.com -p p@ssw0rd -d ~/Desktop/packt -b pdf,epub,mobi,code

## Commandline Options
- *-e*, *--email* = Your login email
- *-p*, *--password* = Your login password
- *-d*, *--directory* = Directory to download into. Default is "media/" in the current directory
- *-b*, *--books* = Assets to download. Options are: *pdf,mobi,epub,code,video, or all*
- *-s*, *--separate* = Create a separate directory for each book
- *-v*, *--verbose* = Show more detailed information
- *-q*, *--quiet* = Don't show information or progress bars

**Book File Types**

- *pdf*: PDF format
- *mobi*: MOBI format
- *epub*: EPUB format
- *code*: Accompanying source code, saved as .zip files
- *video*: .zip file containing the video files and supporting method of viewing them
- *all*: denotes all of the book file types above

I'm working on Python 3.8.4

## Change Log

### 2020-09-28
*.gitignore*
- ignore any file with the .old extension

*main.py*
- Your list of owned books may have duplicates showing more books owned than there should be. Added logic to remove the duplicate books based on productId
- Cleaned up some of the book nameing conventions used by Packt Publishing makeing them a bit more standardized when written to your local machine
- Fixed a small problem with the JWT timestamp checking

### 2020-08-29

*main.py*
- Through some testing, found the Packt Publishing REST API key has a ~15 minute life span. Added a mechanizm to keep track of how long the access key is valid and when it reaches ~14 minutes, refresh the access key.
- Cleaned up the http error reporting by making it a function in main.python
- Rearanged the main function and did some validation of the data prior to creating the folder and downloading the book(s)
- Removed the replacments of spaces for "_" and changed the replacement of : and / to be "-" for easier readability of the foldername and filenames
- Added logic to check for http status code of 404 when attempting to get the book formats as videos may or may not have a code file and return an empty list of book formats

*user.py*
- Add the ability to check the length of time the access key has been alive - Opted to move this logic to main.py, but left it in the user object

### 2020-08-23

*main.py*
- Streamline some of the code
- Check to see if the book has already been downloaded and skip it if it has
- Added the option - b all to denote all book types (code,epub,mobi,pdf, and video)
- The script will now download any videos owned

*config.py*
- Added information regarding other ways to sort the list of books from the PRODUCTS_ENDPOINT URL

*user.py*
- Removed the session timeing from the user object, now handled in main.py
