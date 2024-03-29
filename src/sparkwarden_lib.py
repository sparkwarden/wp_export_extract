#-------------------------------------------------------------
# 
#------------------------------------------------------------

__author__ = 'Gary D. Smith <https://github.com/sparkwarden>'
__version__ = '1.0'
__date__ = '2024/04/28'

"""
Description: Utility library containing simple logging, file list builder,
and list to excel functions.

Tested with Python 3.10
Operating System: iPadOS 17.4
iOS Python apps: Pythonista, a-Shell

Required modules:
 openpyxl - generate excel report file.
 
"""

#---------------------------------------------------------------------
#
#---------------------------------------------------------------------


__all__ = ['Simple_Logger','build_file_list','list_to_xlsx','LF']
	

#---------------------------------------------------------------------
# 
#---------------------------------------------------------------------

import pathlib
import datetime
import io
import sys
import openpyxl


LF = '\n'

#-------------------------------------------------------------
# 
#-------------------------------------------------------------

def get_output_path_with_dt(prefix='simple_logger', extention='.log',\
	timefmt='%Y%m%d_%H%m%S%f'):
	return prefix + '_' + datetime.datetime.now().strftime(timefmt) + extention
			
			
#-------------------------------------------------------------
# 
#-------------------------------------------------------------


class Simple_Logger:
	"""
	lightweight alternative for logging module 
	"""
	
	logger_list = []
	
	PRN_SCREEN_AND_FILE = 1
	PRN_SCREEN_ONLY = 2
	PRN_FILE_ONLY = 3
	PRN_FLUSH_LOG_THRESHOLD = 100
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	def __init__(self, name, prefix, prn_flag=1):
		
		self.is_active = False
		self.name = name
		self.prn_flag = prn_flag
		self.log_cnt = 0
			
		self.logfilepath = get_output_path_with_dt(prefix, '.log')
			
		self.logbuf = io.StringIO()
			
		if self not in Simple_Logger.logger_list:
			Simple_Logger.logger_list.append(self)
			msg = f'\nLogger {self.name} starting. . .\n'
			with open(self.logfilepath,'w',encoding='utf-8') as f:
				f.write('')
				self.writelog(msg)
		else:
			raise Exception ('Logger already established')
			
		self.is_active = True
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	@classmethod
	def get_logger_by_name(cls, name):
		
		node_list = [nd for nd in cls.logger_list if nd.name == name]
		retnode = None
		if len(node_list) > 0:
			retnode = node_list[0]
		return retnode
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	def writelogarg(self, arg):
		"""
		Write arg string to log buffer.  If log threshold reached,
		flush buffer to log file.
		"""
		if self.log_cnt >= Simple_Logger.PRN_FLUSH_LOG_THRESHOLD:
			self.flushlog()
		
		arg_str = str(arg)
		if self.prn_flag == Simple_Logger.PRN_SCREEN_AND_FILE:
			self.logbuf.write(arg_str)
			sys.stdout.write(arg_str)
		elif self.prn_flag == Simple_Logger.PRN_SCREEN_ONLY:
			sys.stdout.write(arg_str)
		else:
			self.logbuf.write(arg_str)
		self.log_cnt+=1
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	def writelog(self, *args):
		for arg in args:
			arg_str = str(arg)
			self.writelogarg(arg_str)
			
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
			
	def flushlog(self):
		with open(self.logfilepath,'a',encoding='utf-8') as f:
			f.write(self.logbuf.getvalue())
		self.log_cnt = 0
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------

	def closelog(self):
		self.writelog(f'\nLogger {self.name} closing. . .')
		self.flushlog()
		self.logbuf.close()
		self.is_active = False
	
	#-------------------------------------------------------------
	# 
	#------------------------------------------------------------
	
	@classmethod
	def writelog_by_name(cls, *args, name='root'):
		logr = cls.get_logger_by_name(name)
		logr.writelog(*args)
		
	#-------------------------------------------------------------
	# 
	#------------------------------------------------------------
		
	@classmethod
	def setup(cls):
		cls.logger_list.clear()
		
	#-------------------------------------------------------------
	# 
	#------------------------------------------------------------
		
	@classmethod
	def shutdown(cls):
		for lg in cls.logger_list:
			if lg.is_active:
				lg.closelog()
	
			
#-------------------------------------------------------------
# 
#-------------------------------------------------------------

def list_to_xlsx(xls_list,xls_path):
	"""
	Write list to excel .xlsx file
	"""
	
	wb = openpyxl.Workbook()
	ws = wb.active
	
	for row in xls_list:
		ws.append(row)

	wb.save(xls_path)
		
#-------------------------------------------------------------
# 
#-------------------------------------------------------------

def build_file_list(startdir:str=None, ptrnstr='*.*') -> list:
	"""
	Return a list of files recursively, starting with
	[startdir] directory, matching [ptrnstr] search pattern.
	"""
	_file_list = []
	
	if startdir is None:
		_startdir = str(pathlib.Path().cwd())
	else:
		_startdir = startdir
	
	p = pathlib.Path(_startdir)
	
	glob_list = p.rglob(ptrnstr)
	
	for path in glob_list:
		_path = str(path)
		p = pathlib.Path(_path)
		
		if p.is_file(): 
			_file_list.append(_path)
	
	return _file_list

#-------------------------------------------------------------
# 
#-------------------------------------------------------------
		
def main(logr):
	
	#-------------------------------------------------------------
	# 
	#------------------------------------------------------------
	
	curdir = pathlib.Path().cwd()
	
	file_list = build_file_list(curdir, '*.py')
	
	logr.writelog(f'{LF} {len(file_list)} .py files in {curdir} tree. {LF}')
	
	#-------------------------------------------------------------
	# 
	#------------------------------------------------------------
	
	
#-------------------------------------------------------------
# 
#------------------------------------------------------------

if __name__ == "__main__":
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	mylogprefix = str(pathlib.Path(__file__).stem)
	
	Simple_Logger.setup()
	
	logr = Simple_Logger(name='root',prefix=mylogprefix)
	
	logr.writelog(f'{LF}program {__file__} started. {LF}')
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	main(logr)
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	logr.writelog(LF)
	logr.writelog(f'{LF}program {__file__} completed. {LF}')
	
	logr.closelog()
	
	Simple_Logger.shutdown()
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------

