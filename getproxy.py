#-*-coding:utf-8-*-
import time
import download
import json
import requests
import threading


ok_proxies = []

def testProxy(proxy, url, delay):
		global ok_proxies
		print 'Test proxy:', proxy
		last_one = time.time()
		# 对ip进行访问url时间判断，时间超出的进行剔除 1秒以上的
		page = download.download(url=url, proxy=proxy)
		if time.time()-last_one <= delay and page is not None:
			ok_proxies.append(proxy)
			print proxy, 'is ok, add it to pool.'
		else:
			print proxy, 'is bad, discard it.'


def testProxies(proxies, url, delay=15.0):
	global ok_proxies
	threads = []
	while proxies:

		for thread in threads:
			if not thread.is_alive():
				threads.remove(thread)

		while len(threads) < 10 and proxies:
			proxy = proxies.pop()
			thread = threading.Thread(target=testProxy, args=(proxy, url, delay))
			thread.setDaemon(True) #ctrl + c can exit
			thread.start()
			threads.append(thread)
		time.sleep(1)
	time.sleep(10) # wait all thread finish
	return ok_proxies


def getProxies(protocol=2):
	r = requests.get('http://127.0.0.1:8000/?protocol=%d'%protocol) # 从代理ip池取出ip
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
			proxies.append(proxy)
	return proxies


def getOkProxies(url, delay=15.0, protocol=2):
	proxies = getProxies(protocol)
	return testProxies(proxies, url, delay)


if __name__ == "__main__":
	print getOkProxies('https://blog.csdn.net/')