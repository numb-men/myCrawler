import download, linkload, getproxy
from bs4 import BeautifulSoup
import time
import csv
import re
import os


def get_books_as_sort():
	url = 'https://www.23wxw.cc'
	seed_url = 'https://www.23wxw.cc/xiaoshuodaquan/'
	page = download.localPage(seed_url)
	if page is None:
		print 'Local file is None, just download.'
		page = download.download(seed_url, save=True)
	else:
		print 'Use local file.'

	soup = BeautifulSoup(page, 'html.parser')
	books_sort = {}
	all_sorts = soup.find('table', class_= 'layui-table').find('tbody').find('tr').find_all('td')
	for a_sort in all_sorts:
		sort_a = a_sort.find('a')
		sort_name = sort_a.text
		sort_link = url + sort_a['href']
		sort_page = download.download(sort_link)
		soup_a_sort = BeautifulSoup(sort_page, 'html.parser')
		books_a_sort = soup_a_sort.find('div', class_='novellist').find('ul').find_all('li')
		books_a_sort_ = []
		for a_book in books_a_sort:
			book_a = a_book.find('a')
			a_book_ = {}
			a_book_[u'name'] = book_a.text.encode('utf-8')
			a_book_[u'link'] = url + book_a['href'].encode('utf-8')
			books_a_sort_.append(a_book_)
		books_sort[sort_name] = books_a_sort_
		time.sleep(3)

	return books_sort


def save_books(books_sort): # save books
	for sort in books_sort:
		with open('dingdian/%s.csv' % sort, 'w') as csvfile:
			fieldnames = [u'name', u'link']
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writeheader()
			for a_book in books_sort[sort]:
				writer.writerow(a_book)
	print 'All books have save.'


def load_local_books(): # load boos from local
	books = {}
	for csvf in find_csvf():
		name = csvf.split('.csv')[0]
		a_sort = []
		with open(csvf, 'r') as csvfile:
			reader = csv.DictReader(csvfile)
			for row in reader:
				a_sort.append(row)
		books[name] = a_sort
	return books


def find_csvf(): # find files which end with .csv
	files = os.listdir('dingdian')
	csvf = []
	for file in files:
		if re.search('\.csv$', file, re.U):
			csvf.append(file)
	return csvf


def get_all_chapter(book_url):
	b_page = download.download(book_url)
	b_soup = BeautifulSoup(b_page, 'html.parser')
	dt = b_soup.find(id='list').find('dl').find_all('dt')[1]
	dds = dt.find_next_siblings('dd')
	chapters = []
	for dd in dds:
		a_chapter = {}
		chapter_a = dd.find('a')
		a_chapter[u'name'] = chapter_a.text.encode('utf-8')
		a_chapter[u'link'] = u'https://www.23wxw.cc' + chapter_a['href'].encode('utf-8')
		chapters.append(a_chapter)
	return chapters


def save_chapters(chapters):
	with open('dingdian/test/test.csv', 'w') as csvfile:
		fieldnames = [u'name', u'link']
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
		writer.writeheader()
		for a_chapter in chapters:
			writer.writerow(a_chapter)
	print 'All chapters have save.'


def load_a_chapter(chapter_name, chapter_url):
	c_page = download.download(chapter_url)
	c_soup = BeautifulSoup(c_page, 'html.parser')
	c_content = c_soup.find(id='content')
	nouse = c_content.find('p')
	nouse.decompose() # delete this tag
	nouse = c_content.find('div')
	nouse.decompose()
	c_content = c_soup.find(id='content').get_text('\n')
	with open('dingdian/test/%s.txt'%chapter_name.decode('utf-8'), 'w') as f:
		f.write(c_content.encode('utf-8'))


if __name__ == '__main__':
	# save_books(get_books_as_sort())

	# print find_csvf()
	
	# get_all_chapter('https://www.23wxw.cc/html/18761/')

	chapters = get_all_chapter('https://www.23wxw.cc/html/109557/')
	for chapter in chapters:
		load_a_chapter(chapter['name'], chapter['link'])