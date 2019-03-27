#-*-coding:utf-8-*-
import download
import time
import threading
import csv
from StringIO import StringIO
from bs4 import BeautifulSoup
import re
import lxml.html
import os, sys

class Load_books:

	def __init__(self, index=0, retry=1000, books_num=10, max_thrad=10, save=False):
		self.index = index
		self.retry = retry
		self.books_num = books_num
		self.max_thrad = max_thrad
		self.save = save
		self.has_load = 0
		self.last_suc = index
		self.threads = []
		self.SLEEP_TIME = 0.5

	def __call__(self): # 线性爬虫
		while self.has_load < self.books_num:
			for thread in self.threads:
				if not thread.is_alive():
					self.threads.remove(thread)
			if self.index-self.last_suc > self.retry:
				print 'I think there is not book to download, just stop.'
				print 'Have downloaded %d books.'
				break
			while len(self.threads) < self.max_thrad:
				thread = threading.Thread(target=self.load_a_book)
				self.index += 1
				thread.setDaemon(True) #ctrl + c can exit
				thread.start()
				self.threads.append(thread)
			time.sleep(self.SLEEP_TIME)

	def load_books_list(self): # 从网站地图爬取
		seed_url = 'http://www.yunxs.com/sitemap.html'
		page = download.localPage(seed_url)
		if page is None:
			print 'Local file is None, just download.'
			page = download.download(seed_url, save=True)
		else:
			print 'Use local file.'
		soup = BeautifulSoup(page, 'html.parser')
		books_sort = {}
		s = soup.findAll(attrs={'class', 'linkbox'})
		for ss in s:
			t = ss.find('h3')
			if t: t = t.find('a')
			if t:
				sort = t.text
				books_sort[sort] = []
				f = ss.find(attrs={'class', 'f6'})
				if f: f = f.findAll('li')
				if f:
					for li in f:
						a = li.find('a')
						if a:
							href = a['href']
							if re.match('\/txt\/', href):
								a_book = {}
								a_book[u'title'] = a.text.split(u'txt下载')[0].encode('utf-8')
								a_book[u'download_href'] = u'http://www.yunxs.com' + href
								books_sort[sort].append(a_book)
		self.save_books(books_sort)
		print 'Have download all books as csv files save ok!'

	def save_books(self, books_sort): # 分类保存成csv表格
		for sort in books_sort:
			with open(sort + '.csv', 'w') as csvfile:
				fieldnames = [u'title', u'download_href']
				writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
				writer.writeheader()
				for a_book in books_sort[sort]:
					writer.writerow(a_book)
		print 'All have save.'

	def load_local_books(self): # 从本地读取所有csv表格
		books = {}
		for csvf in self.find_csvf():
			name = csvf.split('.csv')[0]
			a_sort = []
			with open(csvf, 'r') as csvfile:
				reader = csv.DictReader(csvfile)
				for row in reader:
					a_sort.append(row)
			books[name] = a_sort
		return books

	def get_load_link(self, url): # 将一个链接转换为真实下载链接
		page = download.download(url)
		tree = lxml.html.fromstring(page)
		return u'http://www.yunxs.com' + tree.cssselect('.read_btn>.down>a')[0].get('href')

	def load_a_book(self): # 下载一本书
		book = download.download('http://www.yunxs.com/download/download.php?filetype=txt&filename={}'.format(self.index), noprint=False)
		if book is not None:
			print 'The book with number %d have downloaded!' % self.index
			if self.save:
				with open('{}.txt'.format(self.index), 'w') as f:
					f.write(book)
		self.last_suc = self.index
		self.has_load += 1

	def find_csvf(self): # 查询并返回所有后缀为.csv的文件名列表
		files = os.listdir('.')
		csvf = []
		for file in files:
			if re.search('\.csv$', file, re.U):
				csvf.append(file)
		return csvf


def replace_to_real_dlink(): # 读取本地表格，并全部替换为真实下载链接

	L = Load_books()
	books_ = L.load_local_books()
	books = {}
	for b in books_:
		books[b] = [] # set a null books dict to save replace ok link

	def get_load_link(books, a_sort, book):
		url = book[u'download_href']
		page = download.download(url)
		tree = lxml.html.fromstring(page)
		book[u'download_href']  = u'http://www.yunxs.com' + tree.cssselect('.read_btn>.down>a')[0].get('href')
		books[a_sort].append(book)

	for a_sort in books_:
		books_in_sort = books_[a_sort]
		threads = []
		while len(books_in_sort) > 0:
			for thread in threads:
				if not thread.is_alive():
					threads.remove(thread)
			# if this sort also have book
			while len(threads) < 50 and len(books_in_sort) > 0:
				book = books_in_sort.pop()
				thread = threading.Thread(target=get_load_link, args=(books, a_sort, book))
				thread.setDaemon(True)
				thread.start()
				threads.append(thread)

			time.sleep(0.3)
	time.sleep(10) # wait all thread finish
	L.save_books(books)
	print 'Replace all download_href to real download_href succeed!'

if __name__ == '__main__':
	# data = download.download('http://www.yunxs.com/download/download.php?filetype=txt&filename=1000')
	# str_data = StringIO(data)
	# with open('1000.txt', 'a+') as f:
	# 		f.write(str_data.read())
	
	# L = Load_books(index=500, save=True, books_num=100)
	# L()

	# L = Load_books()
	# # L.load_books_list()
	# print L.load_local_books()
	# L.save_books(books)

	# print L.get_load_link('http://www.yunxs.com/txt/yijianfeixian.html')
	# print L.get_load_link('http://www.yunxs.com/txt/xianjieguilai.html')
	# print L.get_load_link('http://www.yunxs.com/txt/hanmenzhuangyuan.html')
	# print L.get_load_link('http://www.yunxs.com/txt/zuiqiangsanguohuangdixitong.html')

	# replace_to_real_dlink()
	pass
	