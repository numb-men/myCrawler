#-*-coding:utf-8-*-
import download
import linkload
import getproxy
from datetime import datetime
import time
import copy
import thread
from bs4 import BeautifulSoup
import re
import random

proxies, p_unused = [], []
begin_time = time.time()
pv = 0 #记录总访问量


def look_articles(articles, proxy=None):
	""" 单个代理IP的爬取线程
	"""
	global pv
	haslook = []
	for article in articles:
		if article not in haslook:
			haslook.append(article)
			# file_name = 'C:/Users/le/Desktop/my_csdn_blog/%s.html' % str(len(hasload))
			if download.download(article, proxy=proxy):
				pv += 1
	callback(proxy)


def get_articles_links(articles):
	return [arti['link'] for arti in articles]

def get_articles_info(name, articles_num=-1, read_less_n=-1):
	url = 'https://blog.csdn.net/' + name
	page = download.download(url)
	articles = []
	while page is None:
		page = download.download(url)
		time.sleep(1)
	base_url = linkload.getbyre(page, 'var\sbaseUrl\s=\s["\'](\S+)["\']')[0] # 获取分页的url
	pagesize = int(linkload.getbyre(page, 'var\spageSize\s=\s(\d+)')[0]) # 获取每页文章数
	pagesnum = int(linkload.getbyre(page, 'var\slistTotal\s=\s(\d+)')[0]) # 获取总文章数
	print base_url, pagesize, pagesnum
	listnum = pagesnum // pagesize + 2 # 获取页数
	if articles_num < 0: articles_num = pagesnum # 确定爬取的文章数
	for lp in range(1, listnum):
		list_url = base_url + '/' + str(lp)
		page_i = download.download(list_url)
		while page_i is None:
			page_i = download.download(list_url)
			time.sleep(1)
		soup = BeautifulSoup(page_i, 'html.parser')
		artis = soup.find_all('div', class_='article-item-box csdn-tracking-statistics')
		for arti in artis:
			a_article = {}
			link = arti.h4.a['href']
			if re.match('https:\/\/blog\.csdn\.net\/' + name, link):
				a_article['link'] = link
				a_article['id'] = arti['data-articleid']
				info = arti.find(class_='info-box d-flex align-content-center').find_all('p')
				a_article['date_time'] = datetime.strptime(info[0].span.text, "%Y-%m-%d %H:%M:%S")
				a_article['read_num'] = int(info[1].span.text.split(u'阅读数：')[1])
				a_article['comment_num'] = int(info[2].span.text.split(u'评论数：')[1])
				if a_article not in articles:
					articles.append(a_article)
	print len(articles), read_less_n
	# 清除阅读量 > 筛选值的文章
	_articles = []
	if read_less_n > 0:
		for arti in articles:
			if arti['read_num'] < read_less_n:
				_articles.append(arti)
	else: _articles = articles

	# 从所有文章中随机去除几篇文章，以达到所需数量
	for i in range(len(_articles) - articles_num):
		arti = random.choice(_articles)
		_articles.remove(arti)
	return _articles


def callback(proxy):
	""" 让线程爬取完数据之后，进行一个反馈，用于判断爬取结束
	"""
	global p_unused
	if proxy in p_unused:
		p_unused.remove(proxy)
		print u'\n\n线程       [', proxy, u']爬取结束!\n剩余：', len(p_unused), '\n'
		print u'累计获取访问量： ', pv
		if not p_unused:
			print u'\n\n所有线程爬取结束！'
			print u'耗时： ', (time.time()-begin_time) / 60 , u'分钟\n\n'


def lookmyblog(name, times=-1, articles_num=-1, read_less_n=-1):
	global proxies, p_unused, begin_time
	url = 'https://blog.csdn.net/'
	proxies = getproxy.getOkProxies(url)
	p_unused = copy.deepcopy(proxies)
	while True:
		articles = get_articles_links(get_articles_info(name, articles_num=articles_num, read_less_n=read_less_n))
		if times == 0: break
		begin_time = time.time()
		for proxy in proxies:
			try: 
				print u'开启新线程...'
				thread.start_new_thread(look_articles, (articles, proxy)) # 开启一个新线程
				time.sleep(1600/len(proxies)) # 时间不是关键，所以放慢速度
			except: 
				print u"出现未知异常"
		proxies = getproxy.getOkProxies('https://blog.csdn.net/') # 刷新代理池
		p_unused = copy.deepcopy(proxies)
		times -= 1


if __name__ == '__main__':
	# articles = get_articles_info('le_17_4_6', read_less_n=700)
	# print get_articles_links(articles)
	# print len(articles)
	# print articles
	lookmyblog('le_17_4_6')
