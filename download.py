#-*-coding:utf-8-*-
import urllib, urllib2, time, json, random, traceback, sys

def download(url, data_dict=None, req_type='GET', timeout=15, num_retries=3, proxy=None, local_file=None, save=False, noprint=False):
	""" 下载html
		url 				网页地址
		data_dict 			请求附带的字典数据，默认不附带数据
		req_type 			请求类型，默认GET
		timeout 			超时时间，默认2秒
		num_retries 		尝试次数，默认尝试三次
		useProxy			是否使用代理，默认不使用
		local_file 			保存的全路径，默认和代码同路径下
		save 				是否进行保存，默认false不保存
	"""
	if noprint:
		f = open('download.log', 'w')
		sys.stdout = f
	print '\nBegin download:', url
	page, req = None, None
	headers = {
		'Referer': 'https://www.baidu.com', 
		'Connection': 'keep-alive', 
		'User-agent': get_user_agent(), 
		} 
	if req_type == 'GET': #使用get
		if data_dict:
			data_pass = urllib.urlencode(data_dict) # 将数据打包成GET格式
			url = url + '?' + data_pass
			data_dict = None
		req = urllib2.Request(url, headers=headers)

	elif req_type == 'POST': #使用post
		if data_dict:
			data_pass = urllib.urlencode(data_dict)
			req = urllib2.Request(url, data_pass, headers=headers)
	try:
		opener = urllib2.build_opener()
		if proxy is not None:
			opener.add_handler(urllib2.ProxyHandler(proxy))
		if req_type == 'GET':
			rep = opener.open(req, timeout=timeout)
		elif req_type == 'POST':
			rep = opener.open(req, data=json.dumps(data_dict), timeout=timeout) # 数据要用json打包再post发送

	except urllib2.URLError as ue: #访问错误
		if hasattr(ue, 'code'):
			print 'Fail download :', url, ue.code
			if num_retries > 0 and 500 <= ue.code < 600:
				# 当报错原因是因为服务器繁忙时尝试再次下载，ue.reason()可以获取错误原因
				time.sleep(timeout)
				print 'Retry it      :', url, ue.code
				return download(url, num_retries=num_retries-1)
		elif hasattr(ue, 'reason'):
			print 'Cant connect server:', ue.reason
		else:
			print 'Dont exist:', url

	except ValueError as ve: #地址不合法
		print 'Invalid url:', url

	except Exception, e:
		print 'Mabe Timeout or some orther error'

	else:
		r_url = rep.geturl() # 有时候网页重定向，这样可以获取到实际访问的地址
		try: page = rep.read() # 获取网页
		except: print 'Mabe Timeout or some orther error'
		else:
			code = rep.getcode() # 获取状态码
			# hms = rep.info
			rep.close()
			print 'Succeed download!', r_url, code

	if save and page is not None: # 如果需要保存的话
		savePage(url, page, local_file)

	return page

def get_user_agent():
	USER_AGENTS = [
		"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
		"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
		"Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
		"Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
		"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
		"Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
		"Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
		"Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
		"Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
		"Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
		"Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
		"Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
		"Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
		"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
		"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
		"Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
		"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11",
		"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER",
		"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; LBBROWSER)",
		"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)",
		"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 LBBROWSER",
		"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
		"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)",
		"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
		"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; 360SE)",
		"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
		"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
		"Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
		"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
		"Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5",
		"Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13pre",
		"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0",
		"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
		"Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10"
	]
	return USER_AGENTS[random.randint(0, len(USER_AGENTS)-1)]

def localPage(url):
	local_file = url.replace("/", "@1").replace(":", "@2").replace('.', '@3').replace('?', '@4') + '.html'
	page = ""
	try:
		with open(local_file, "rb") as f:
			page = f.read()
	except:
		return None
	return page

def savePage(url, page, local_file= None):
	""" 将获取的网页保存
	"""
	try:
		if local_file is None: # 如果提供的地址为空，即默认状态，保存到程序所属的文件下
			local_file = url.replace("/", "@1").replace(":", "@2").replace('.', '@3').replace('?', '@4') + '.html'
		with open(local_file,"wb") as f:
			f.write(page)
	except IOError as ioe:
		print 'Fail save %s %s' % (local_file, traceback.format_exc())
		return None
	else:
		print 'Succeed save ', local_file
		return local_file

if __name__ == "__main__":
	# download('https://toutiao.china.com/')
	# download('https://www.cnblogs')
	# download('false url')
	# download('http://httpstat.us/500')

	# download('https://www.cnblogs.com/ygh1229/p/6586523.html', save=True)
	# download('http://www.fjtyze.cn/', save=True)
	# download('http://www.fjtyze.cn/', local_file='D:/www_fjtyze_cn.txt', save=True)
	# download('https://www.guazi.com/fz/sell', req_type='GET', data_dict={'ca_s':'sem_sogoucx','ca_n':'cxgzsh_sell3','scode':'10103106712'}, save=True)
	# download('https://www.guazi.com/fz/sell', req_type='POST', data_dict={'ca_s':'sem_sogoucx','ca_n':'cxgzsh_sell3','scode':'10103106712'}, save=True)
	# download('http://toutiao.china.cn/', save=True, local_file='D:/toutiao.html')

	# download('https://blog.csdn.net/le_17_4_6', save=True)
	# print localPage('https://blog.csdn.net/le_17_4_6')
	pass