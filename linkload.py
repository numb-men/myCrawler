#-*-coding:utf-8-*-
import download, getproxy
import socket
import builtwith 				# builtwith识别网页的开发技术，builtwith.parse('http://example.com')
import urlparse 				# 将链接转为绝对链接
from datetime import datetime
import robotparser 				# 爬虫限制文件读取
import Queue 					# 队列
import itertools 				# 迭代器
import requests
import re 						# 正则匹配
from bs4 import BeautifulSoup 	# 解析网页使用
import lxml.html 				# 使用css选择器高效匹配
from lxml import etree 			# 使用xpath

########################################################
#
#	三种网页抓取方式
#	 
#	1、正则表达式 
#	2、BeautifulSoup
#	3、lxml
#	
########################################################
def getbyre(page, re_str='<a[^>]+href=["\'](.*?)["\']'):
	""" 将一个html中的所有链接筛选出来，默认状态只获取链接
	"""
	webpage_regex = re.compile(re_str, re.IGNORECASE)
	return webpage_regex.findall(page) if page else None

def link_crawler(seed_url, link_regex=None, delay=2.0, max_depth=2, max_urls=-1, useProxy=True, local_file=None, save=False):
	""" 将网页中符合line_regex正则表达式的链接都筛选出来:
		seed_url		根链接
		link_regex		匹配的正则规则
		delay			延迟
		max_length		最大深度
		max_urls		最多储存的链接数
		local_file		本地保存路径
		save 			是否保存
	"""

	begin_time = datetime.now()
	pre_time = datetime.now()
	crawl_queue = Queue.deque([seed_url]) # 还需要爬的链接的队列
	seen = {seed_url: {'depth': 0}} # 初始深度为0 seen用来保存链接和遍历深度
	urls_num = 0 # 链接的个数
	pages_num = 0 # 页面的个数
	index_proxise = -1 # 设置代理的index，同时控制是否进行时延
	# rp = get_robots(seed_url) # robot禁止规则
	if useProxy:	# 从代理池获取IP
		proxies = getProxies(url=seed_url, delay=delay, protocol=1)
		get_proxies_time = (datetime.now() - begin_time).seconds
		num_proxise = len(proxies)
	throttle = Throttle(delay) # 速度阀门
	okProxy = useProxy and (num_proxise!=0)

	while crawl_queue: # 遍历链接
		url = crawl_queue.pop()
		if okProxy: #循环获取代理进行遍历
			if index_proxise == num_proxise:
				index_proxise = -1
		try:
			# if rp.can_fetch('Mozilla/5.0 (Windows NT 6.1; Win64; x64)', url):
			if not contain_zh(url): # 防止中文乱码的链接
				if index_proxise == -1: throttle.wait(url) # 进行限速
				depth = seen[url]['depth']
				print u'\n第[', pages_num+1, u']页 已爬取链接数目：', urls_num, u'  深度：', depth
				if okProxy:
					if index_proxise != -1:
						proxy = proxies[index_proxise] #这次使用的代理IP
						page = download(url=url, proxy=proxies[index_proxise])
					else:
						page = download(url) # 使用本机IP访问
					index_proxise += 1
				else:
					page = download(url)
				links = []
				if depth != max_depth:
					links_ = getbyre(page)
					if links_ is not None: # 防止空页面
						if link_regex: # 如果有给正则表达式则进行匹配
							links.extend(link for link in links_ if re.match(link_regex, link))
						else:
							links.extend(link for link in links_)
						for link in links:
							link = normalize(seed_url, link) # 将链接进行规范化，转为绝对链接
							if link not in seen: # 如果链接没有重复
								pre_time = datetime.now()
								a_link = {}
								a_link['depth'] = depth + 1
								seen[link] = a_link # 保存链接
								urls_num += 1
								if same_domain(seed_url, link): # 如果来自同一个域名, 将链接加入遍历队伍中
									crawl_queue.append(link)
				pages_num += 1
		except Exception, e:
			print u'访问超时或其他错误'
		# 如果爬取的链接数目超出上限了或者超过600秒链接数都不再增加，视为已经爬完，避免爬虫陷阱 or (datetime.now() - pre_time).seconds > 600
		if urls_num >= max_urls and max_urls != -1:
			break
	# else:
	# 	print url, u'被robots.txt禁止爬取' 


	all_time = (datetime.now() - begin_time).seconds
	hour = all_time / 3600
	minute = (all_time % 3600) / 60
	second = all_time % 60
	print u'\n下载结束，累计下载链接:', urls_num
	print u'下载开始时间：', begin_time.strftime("%m-%d %H:%M")
	print u'下载结束时间：', datetime.now().strftime("%m-%d %H:%M")
	print u'累计下载时间： %s:%s:%s' % (hour, minute, second)
	page_avg = ((all_time - get_proxies_time)/1.0)/(pages_num/1.0) if useProxy else (all_time/1.0)/(pages_num/1.0)
	print u'平均时延：', page_avg, u'秒/页'
	if useProxy:
		print u'其中查询获取代理花去了', get_proxies_time, u'秒'
	if save: # 如果需要保存的话
		saveLinks(seed_url, seen, local_file)

	return seen

def contain_zh(word):
	""" 判断传入字符串是否包含中文
		:param word: 待判断字符串
		:return: True:包含中文  False:不包含中文
	"""
	try:
		word = word.decode()
		global zh_pattern
		match = zh_pattern.search(word)
	except Exception, e:
		print u'解码错误'
		return False
	else:
		return match

class Throttle:
	""" 一个限制爬虫速度的限流阀
	"""
	def __init__(self, delay):
		self.delay = delay # 延迟时间, 秒
		self.domains = {} # 域名:上一次爬取的时间

	def wait(self, url):
		domain = urlparse.urlparse(url).netloc # 获取域名
		last_accessed = self.domains.get(domain, None)
		# print 'domain:', domain, ' ', last_accessed

		if self.delay > 0 and last_accessed is not None:
			sleep_secs = self.delay - (datetime.now() - last_accessed).total_seconds()
			print 'sleep_secs:', sleep_secs
			if sleep_secs > 0:
				time.sleep(sleep_secs)
		self.domains[domain] = datetime.now()

def normalize(seed_url, link):
	""" 将url补全，去除碎片
	"""
	link, _ = urlparse.urldefrag(link) #将url中的fragment去的，即去掉“#”后面的链接
	return urlparse.urljoin(seed_url, link)

def get_robots(url):
	""" 返回robots.txt中的url限制判断器
	"""
	rp = robotparser.RobotFileParser()
	rp.set_url(urlparse.urljoin(url, '/robots.txt'))
	rp.read()
	return rp

def same_domain(url1, url2):
	""" 判断域名是否一样
	"""
	return urlparse.urlparse(url1).netloc == urlparse.urlparse(url2).netloc

def iteration(url, index_begin=1, index_end=-1, max_errors=5, getPage=False):
	""" 按下标进行排布的链接可以通过这个方法批量获取
	"""
	num_errors = 0
	links = [] if not getPage else {}
	page = None
	for index in itertools.count(index_begin):
		index_url = '%s-%d' % (url, index)
		try: page = download(url)
		except: pass
		if page is not None:
			num_errors = 0
			if not getPage:
				links.append(index_url)
			else:
				links[index_url]= page
		else:
			num_errors += 1
			if num_errors >= max_errors:
				break
		if index == index_end:
			break

	return links

def saveLinks(seed_url, links, local_file=None, withPage=False, rmvb='txt'):
	""" 将链接或者包含page的链接字典按rmvb格式保存到文件
	"""
	# links = {link_i: {depth: d, page: page...}}
	# print links
	try:
		if local_file is None: # 如果提供的地址为空，即默认状态，保存到程序所属的文件下
			local_file = seed_url.replace("/", "_").replace(":", "#").replace('.', '@').replace('?', '$') + '_urls.' + rmvb
		with open(local_file,"wb") as f:
			if rmvb == 'txt':
				for key, values in links.items():
					# (key: valuse)
					if withPage:
						savePage(key, values['page'])
						values['local_file'] = local_file
					f.write(key)
					f.write('\n')
					for keykey, value in values.items():
						if keykey != 'page':
							f.write(('%s: %s\n' % (keykey, str(value))))
					f.write('\n')
				# f.write(str(links))
			else:
				return None
	except IOError as ioe:
		print u'失败保存：%s %s' % (local_file, traceback.format_exc())
		return None
	else:
		print u'成功保存：%s' % local_file
		return local_file

if __name__ == '__main__':
	# 测试get_links()
	page = download.download('https://blog.csdn.net/le_17_4_6/', save=True)
	base_url = getbyre(page, 'var\sbaseUrl\s=\s["\'](\S+)["\']')[0] # 获取分页的url
	pagesize = getbyre(page, 'var\spageSize\s=\s(\d+)')[0] # 获取每页文章数
	pagesnum = getbyre(page, 'var\slistTotal\s=\s(\d+)')[0] #获取总文章数
	print base_url, pagesize, pagesnum
	listnum = int(pagesnum) // int(pagesize) + 2 #获取页数
	links=[]
	for lp in range(1, listnum):
		print lp
		list_url = base_url + '/' + str(lp)
		page_i = download.download(list_url)
		links.extend(getbyre(page_i, re_str='<a[^>]+href=["\'](https:\/\/blog\.csdn\.net\/le_17_4_6\/article\/details\/\d+)["\']'))
	hasload = []
	for link in links:
		if link not in hasload:
			hasload.append(link)
			file_name = 'C:/Users/le/Desktop/my_csdn_blog/%s.html' % str(len(hasload))
			download.download(link, timeout=10, local_file=file_name, save=True)
