#-*-coding:utf-8-*-
import urllib
import urllib2
import socket
import builtwith # builtwith识别网页的开发技术，builtwith.parse('http://example.com')
import json, time, traceback
import urlparse # 将链接转为绝对链接
import re # 正则匹配
from datetime import datetime
import robotparser # 爬虫限制文件读取
import Queue # 队列
import itertools # 迭代器
import requests
from bs4 import BeautifulSoup #解析网页使用
import lxml.html #使用css选择器高效匹配
from lxml import etree #使用xpath

# timeout in seconds, 如果需要设置全局超时时间的话，使用以下两行注释内容
# time_out = 10
# socket.setdefaulttimeout(time_out)

# 初次尝试urllib2的demo小函数
def download_1(url):
	return urllib2.urlopen(url).read() #最基础的下载网页

def download_2(url):
	print 'Downloading:', url
	try:
		page = urllib2.urlopen(url).read()
	except urllib2.URLError as e: #捕获url错误的异常
		print 'Download error:', e.reason
		page = None
	return page

zh_pattern = re.compile(u'[\u4e00-\u9fa5]+')

def contain_zh(word):
	'''
	判断传入字符串是否包含中文
	:param word: 待判断字符串
	:return: True:包含中文  False:不包含中文
	'''
	try:
		word = word.decode()
		global zh_pattern
		match = zh_pattern.search(word)
	except Exception, e:
		print u'解码错误'
		return False
	else:
		return match

def getProxies(url, delay=1.0, protocol=2):
	r = requests.get('http://127.0.0.1:8000/?protocol=%d&country=国内'%protocol) # 从代理ip池取出高匿国内同时支持http/https的ip
	ip_ports = json.loads(r.text)
	proxies= []
	for ip_port in ip_ports:
		if protocol == 0:
			proxy = {
				'http':'http://%s:%s'%(ip_port[0],ip_port[1]),
			}
		elif protocol == 1:
			proxy = {
				'https':'https://%s:%s'%(ip_port[0],ip_port[1]),
			}
		else:
			proxy = {
				'http':'http://%s:%s'%(ip_port[0],ip_port[1]),
				'https':'https://%s:%s'%(ip_port[0],ip_port[1]),
			}
		print u'测试代理IP：', ip_port
		last_one = datetime.now()
		# 对ip进行访问url时间判断，时间超出的进行剔除 1秒以上的
		page = download(url=url, proxy=proxy)
		if (datetime.now() - last_one).total_seconds() <= delay and page is not None:
			proxies.append(proxy)
			print ip_port, u'速度足够，加入池中'
		else:
			print ip_port, u'速度不足，剔除'

	print proxies
	print u'成功获取代理IP数：', len(proxies)
	return proxies

def download(url, data_dict=None, req_type='GET', timeout=2, num_retries=3, proxy=None, local_file=None, save=False):
	'''
	url 				网页地址
	data_dict 			请求附带的数据
	req_type 			请求类型，默认GET
	timeout 			超时时间
	num_retries 		尝试次数
	useProxy			是否使用代理
	local_file 			保存的全路径, 默认和代码同路径下
	save 				是否进行保存，默认false不保存
	'''
	print u'开始下载：', url
	page, req= None, None
	headers = {	# 伪造的http请求的header

		'Referer': 'https://www.baidu.com', 
		# Referer  是  HTTP  请求header 的一部分，当浏览器（或者模拟浏览器行为）向web 服务器发送请求的时候，
		# 头信息里有包含  Referer  。比如我在www.google.com 里有一个www.baidu.com 链接，那么点击这个www.baidu.com ，它的header 信息里就有：
  		# Referer=http://www.google.com
		# 由此可以看出来吧。它就是表示一个来源。
		# 1、防止盗链，比如我只允许我自己的网站访问我自己的图片服务器，那我的域名是www.google.com，
		# 那么图片服务器每次取到Referer来判断一下是不是我自己的域名www.google.com，如果是就继续访问，不是就拦截。

		'Connection': 'keep-alive', 
		# 保持长连接

		'User-agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0', 
		# 伪造的用户代理

		} 
	if req_type == 'GET': #使用get
		if data_dict:
			data_pass = urllib.urlencode(data_dict) # 将数据打包成GET格式
			url=url+'?'+ data_pass
			data_dict= None
		req = urllib2.Request(url, headers=headers)

		'''
		class urllib2.Request(url[, data][, headers][, origin_req_host][, unverifiable])
		URL请求的抽象类
		
		参数：
		url 包含有效URL的字符串
		
		data 参数可能是一个指定了附加发送给服务器数据的字符串，或则是None如果不需要发送。
		在目前，HTTP协议请求是仅有的使用data的请求；HTTP协议请求将会是POST方式而不是GET如果提供了data参数。 
		data 参数应是一个标准的application/x-www-form-urlencoded 格式的缓存(buffer)。 
		urllib.urlopen() 函数接受一个字典或者二元组序列参数然后返回一个上述格式的字符串。
		urllib2组件使用包含 connection：close的头部发送HTTP/1.1请求。
		
		headers 应是一个字典，键值对将被作为参数传递给add_header()。
		这常用于“欺骗” User-Agent 这个头部值，该值被浏览器用于鉴别浏览者。
		一些HTTP服务器仅允许来自普通浏览器的请求而不是脚本。
		比如，Mozilla 的火狐(FireFox)浏览器可能被识别为  Mozilla/5.0 (X11; U; Linux i686) Gecko/20071127 Firefox/2.0.0.11 ，
		而 urllib2 的默认用户代理字符串是 Python-urllib/2.6( python2.6中) 。
		
		origin_req_host 应是最初处理请求的主机，默认是RFC 2965。
		默认等于cookielib.request_host(self)。 这是用户初始化的最开始请求的主机名或IP地址。
		比如请求的是一份HTML 文档中的一幅图片，这应是发起获取含有图片页面的请求方主机子。
		
		unverifiable 应如RFC2965，指明请求是否是无法校验的。
		默认为False。 无法校验的请求的URL是用户无法选择批准通过的 。
		比如，请求包含在HTML文档中的一幅图片，用户无法选择批准自动获取的图片，这时的值true。
		'''

	elif req_type == 'POST': #使用post
		if data_dict:
			data_pass = urllib.urlencode(data_dict)
			req = urllib2.Request(url, data_pass, headers=headers)
	try:
		opener = urllib2.build_opener()
		if proxy is not None:
			opener.add_handler(urllib2.ProxyHandler(proxy))
		if req_type == 'GET':
			rep = opener.open(req, timeout= timeout)
		elif req_type == 'POST':
			rep = opener.open(req, data= json.dumps(data_dict), timeout= timeout) # 数据要用json打包再post发送

		# urllib2.urlopen(url[, data[, timeout[, cafile[, capath[, cadefault[, context]]]]])
		# 
		# 参数：
		# url参数指定的字符串或者Request对象类型的URL链接地址
		# data参数可能是一个指定了附加发送给服务器数据的字符串，或则是None如果不需要发送。
		# 可选的 timeout 指定了一个以秒为单位的超时参数来屏蔽比如尝试链接的操作 (如果没有设定，默认的全局超市设置将会被采用)
		# 可选的 cafile 和 capath 参数明确了一个用于HTTPS请求的受信任CA证书集。cafile应指向单个包含CA证书集的文件，而capath应指向可哈希的证书文件目录。
		# cadefault参数是忽略的。
		# 如果context 存在，它一定是一个描述不同SSL选项的 ssl.SSLContext 实例。查看HTTPSConnection获取更多的细节。
		# 
		# 返回值：
		# geturl() — 返回从URL获取的资源，通常用来判定是否跟随跳转。
		# info() — 以 mimetools.Message 实例的格式返回页面的元数据(meta-information) ，比如头部。(查看 HTTP Headers)
		# getcode() — 返回HTTP响应的状态码。
		# 发生错误的时候以 URLError 报错
		# 
		# 其它：
		# 注意，返回值可能是None，如果没有处理器处理请求(然而默认安装的全局 OpenerDirector使用UnknownHandler来确保请求没有被处理)。
		# 另外，如果代理设置被检测到(比如，当 _proxy environment 变量像 http_proxy被设置)，ProxyHandler 会默认安装来确保请求在整个代理中会被处理。
		# 
		# request.add_header() ：可以添加headers头的一些信息
		
	except urllib2.URLError as ue: #访问错误
		if hasattr(ue, 'code'):
			print u'失败下载：', url, ue.code
			if num_retries > 0 and 500 <= ue.code < 600:
				# 当报错原因是因为服务器繁忙时尝试再次下载，ue.reason()可以获取错误原因
				print u'再次尝试：', url, ue.code
				return download(url, num_retries= num_retries - 1)
		elif hasattr(ue, 'reason'):
			print u'无法连接服务器，原因：', ue.reason
		else:
			print u'不存在  ：', url

	except ValueError as ve: #地址不合法
		print u'不合法  ：', url

	except Exception, e:
		print u'时间超出或其他错误'

	else: # 没有异常
		r_url = rep.geturl() # 有时候网页重定向，这样可以获取到实际访问的地址
		try: page = rep.read() # 获取网页
		except Exception, e: print u'时间超出或其他错误'
		code = rep.getcode() # 获取状态码
		hms = rep.info
		rep.close()
		print u'成功下载：', r_url, code

	if save and page is not None: # 如果需要保存的话
		savePage(url, page, local_file)
		# 	# 异常错误信息的获取：
		# 	#
		# 	# 1、str(e) 返回字符串类型，只给出异常信息，不包括异常信息的类型，如1/0的异常信息
		# 	# 'integer division or modulo by zero'

		# 	# 2、repr(e)给出较全的异常信息，包括异常信息的类型，如1/0的异常信息

		# 	# "ZeroDivisionError('integer division or modulo by zero',)"

		# 	# 3、e.message 获得的信息同str(e)

		# 	# 4、采用traceback模块 需要导入traceback模块，此时获取的信息最全，
		# 	# 与python命令行运行程序出现错误信息一致。使用traceback.print_exc()打印异常信息到标准错误，
		# 	# 就像没有获取一样，或者使用traceback.format_exc()将同样的输出获取为字符串。
		# 	# 你可以向这些函数传递各种各样的参数来限制输出，或者重新打印到像文件类型的对象。
		# else:
		# 	print u'成功保存：',  local_file

	return page

def link_crawler(seed_url, link_regex=None, delay=2.0, max_depth=2, max_urls=-1, useProxy=True, local_file=None, save=False):
	''' 将网页中符合line_regex正则表达式的链接都筛选出来:
		seed_url: 根链接, link_regex: 匹配的正则规则, delay: 延迟,
		max_length: 最大深度, max_urls: 最多储存的链接数,
		local_file: 本地保存路径, save: 是否保存,
	'''
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
					links_ = get_links(page)
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

class Throttle:
	'''一个限制爬虫速度的限流阀
	'''
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
	'''将url补全，去除碎片'''
	link, _ = urlparse.urldefrag(link) #将url中的fragment去的，即去掉“#”后面的链接
	return urlparse.urljoin(seed_url, link)

def get_robots(url):
	'''返回robots.txt中的url限制判断器
	'''
	rp = robotparser.RobotFileParser()
	rp.set_url(urlparse.urljoin(url, '/robots.txt'))
	rp.read()
	return rp

def same_domain(url1, url2):
	return urlparse.urlparse(url1).netloc == urlparse.urlparse(url2).netloc
	'''ParseResult(scheme='http', netloc='localhost', path='/test.py', params='', query='a=hello&b=world ', fragment='')
		result.scheme : 网络协议
		result.netloc: 服务器位置（也有可能是用户信息）
		result.path: 网页文件在服务器中的位置
		result.params: 可选参数
		result.query: &连接键值对
	'''

def get_links(page):
	'''将一个html中的所有链接筛选出来
	'''
	webpage_regex = re.compile('<a[^>]+href=["\'](.*?)["\']', re.IGNORECASE)
	return webpage_regex.findall(page) if page else None
	# page = etree.HTML(html.lower().decode('utf-8'))
	# hrefs = page.xpath(u"//a")
	# return hrefs

def iteration(url, index_begin= 1, index_end= -1, max_errors= 5, getPage= False):
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

def savePage(url, page, local_file= None):
	""" 将获取的网页保存进入目录
	"""
	try:
		if local_file is None: # 如果提供的地址为空，即默认状态，保存到程序所属的文件下
			local_file = url.replace("/", "_").replace(":", "#").replace('.', '@').replace('?', '$') + '.html'
		with open(local_file,"wb") as f:
			f.write(page)
	except IOError as ioe:
		print u'失败保存：%s %s' % (local_file, traceback.format_exc())
		return None
	else:
		print u'成功保存：', local_file
		return local_file

def saveLinks(seed_url, links, local_file= None, withPage=False, rmvb= 'txt'):
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
	# 测试数据
	# print download_1('https://toutiao.china.com/')
	# print download_1('http://www.fjtyze.cn/')
	# print download_2('https://www.cnblogs.com/ygh1229/p/6586523.html')
	# print download_2('false url')
	# download('https://toutiao.china.com/')
	# download('http://www.fjtyze.cn/')
	# download('https://www.cnblogs.com/ygh1229/p/6586523.html')
	# download('https://www.cnblogs')
	# download('false url')
	# download('http://httpstat.us/500')
	# print builtwith.parse('https://www.cnblogs.com/ygh1229/p/6586523.html')
	# print builtwith.parse('http://www.fjtyze.cn/')
	# print builtwith.parse('https://toutiao.china.com/')
	# download('https://www.cnblogs.com/ygh1229/p/6586523.html', save=True)
	# download('http://www.fjtyze.cn/', save=True)
	# download('http://www.fjtyze.cn/', local_file='D:/www_fjtyze_cn.txt', save=True)
	# download('https://www.guazi.com/fz/sell', req_type = 'GET', data_dict={'ca_s':'sem_sogoucx','ca_n':'cxgzsh_sell3','scode':'10103106712'}, save=True)
	# download('https://www.guazi.com/fz/sell', req_type = 'POST', data_dict={'ca_s':'sem_sogoucx','ca_n':'cxgzsh_sell3','scode':'10103106712'}, save=True)
	# download('http://toutiao.china.cn/', save=True, local_file='D:/toutiao.html', )
	# print get_links(download('http://www.fjtyze.cn/', save=True))
	# print get_links(download('https://www.cnblogs.com'))
	# link_crawler(seed_url='https://www.cnblogs.com', delay=2, max_urls=1000, max_depth=3, local_file='D:/www_cnblogs_com_urls.txt', save=True)
	# link_crawler(seed_url='https://www.cnblogs.com', delay=1, max_urls=1000000, max_depth=20, local_file='D:/www_cnblogs_com_urls.txt', save=True)
	# link_crawler(seed_url='http://www.fjtyze.cn/', delay=-1, max_urls=-1, max_depth=-1)
	# link_crawler(seed_url='http://www.fjtyze.cn/', useProxy=False, delay=-1, max_urls=-1, max_depth=-1, save=True)
	# r = requests.get('http://127.0.0.1:8000/?types=0&country=国内')
	# ip_ports = json.loads(r.text)
	# print ip_ports
	# ip = ip_ports[0][0]
	# port = ip_ports[0][1]
	# proxies={
	# 	'http':'http://%s:%s'%(ip,port),
	# 	'https':'http://%s:%s'%(ip,port)
	# }
	# r = requests.get('http://ip.chinaz.com/',proxies=proxies)
	# r.encoding='utf-8'
	# print r.text
	# print getProxies()
	# proxy = getProxies()[0]
	# print proxy
	# r = requests.get('http://ip.chinaz.com/', proxies=proxy)
	# print r.text
	# download(url='https://www.cnblogs.com', proxy=proxy, save=True)
	# link_crawler(seed_url='https://www.cnblogs.com', delay=1.5, max_urls=-1, max_depth=20, useProxy=True, local_file='D:/cnblogs_urls_use_proxy.txt', save=True)
	# link_crawler(seed_url='https://www.cnblogs.com', delay=1.0, max_urls=500, max_depth=3, useProxy=False, local_file='D:/cnblogs_urls.txt', save=True)
	# link_crawler(seed_url='http://www.fjtyze.cn/', delay=1.0, max_urls=-1, max_depth=-1, useProxy=True, local_file='D:/fjtyze_urls_use_proxy.txt', save=True)
	link_crawler(seed_url='https://blog.csdn.net/le_17_4_6/', delay=10.0, max_urls=-1, max_depth=5, useProxy=True, local_file='D:/my_csdn_urls.txt', save=True)
	
	
	
	