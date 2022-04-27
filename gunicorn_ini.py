import gevent.monkey
import multiprocessing

gevent.monkey.patch_all()

bind = '0.0.0.0:5001'
workers = multiprocessing.cpu_count() * 2 + 1
