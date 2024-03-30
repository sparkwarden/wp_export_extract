#-------------------------------------------------------------
# 
#------------------------------------------------------------

__author__ = 'Gary D. Smith <https://github.com/sparkwarden>'
__version__ = '1.0'
__date__ = '2024/04/28'

"""
Description: Utility library containing message writer, file list builder,
and list-to-excel functions.

Tested with Python 3.10
Operating System: iPadOS 17.4
iOS Python apps: Pythonista, a-Shell

Required modules:
 openpyxl - to generate excel report file.
 
"""

#---------------------------------------------------------------------
#
#---------------------------------------------------------------------


__all__ = ['Message_Writer','build_file_list','list_to_xlsx','LF']
	

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

class Message_Writer:
	"""
	Output Messages to File.
	"""
	
	node_list = []
	
	PRN_SCREEN_AND_FILE = 1
	PRN_SCREEN_ONLY = 2
	PRN_FILE_ONLY = 3
	PRN_FLUSH_LOG_THRESHOLD = 100
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	def __init__(self, name, prefix, prn_flag=1):
		
		_cls = Message_Writer
		
		self.is_active = False
		self.name = name
		self.prn_flag = prn_flag
		self.msg_cnt = 0
			
		self.msgfilepath = _cls.get_output_path_with_dt(prefix)
			
		self.msgbuf = io.StringIO()
			
		if self not in _cls.node_list:
			_cls.node_list.append(self)
			msg = f'\nmessage writer [{self.name}] starting. . .\n'
			with open(self.msgfilepath,'w',encoding='utf-8') as f:
				f.write('')
				self.write_msg(msg)
		else:
			raise Exception ('message writer already established')
			
		self.is_active = True
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	@staticmethod
	def get_output_path_with_dt(prefix='msgr', ext='.log',\
		_timefmt='%Y%m%d_%H%m%S%f'):
		_path = ''.join([prefix, '_', datetime.datetime.now().strftime(_timefmt), ext])
		return _path
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	@classmethod
	def get_writer_by_name(cls, name):
		
		_node_list = [nd for nd in cls.node_list if nd.name == name]
		retnode = None
		if len(_node_list) > 0:
			retnode = _node_list[0]
		return retnode
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	def write_msg(self, *args):
		"""
		write msg to buffer.
		"""
		_arg_str = ''
		for arg in args:
			_arg_str += str(arg)
		
		_cls = Message_Writer
		
		if self.msg_cnt >= _cls.PRN_FLUSH_LOG_THRESHOLD:
			self.flushbuf()
		
		if self.prn_flag == _cls.PRN_SCREEN_AND_FILE:
			self.msgbuf.write(_arg_str)
			sys.stdout.write(_arg_str)
		elif self.prn_flag == _cls.PRN_SCREEN_ONLY:
			sys.stdout.write(_arg_str)
		else:
			self.msgbuf.write(_arg_str)
			
		self.msg_cnt+=1
		
			
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
			
	def flushbuf(self):
		"""
		write the msgbuf to file.
		"""
		with open(self.msgfilepath,'a',encoding='utf-8') as f:
			f.write(self.msgbuf.getvalue())
		self.msg_cnt = 0
		
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------

	def close_writer(self):
		self.write_msg(f'\nmessage writer [{self.name}] closing. . .')
		self.flushbuf()
		self.msgbuf.close()
		self.is_active = False
	
	#-------------------------------------------------------------
	# 
	#------------------------------------------------------------
		
	@classmethod
	def setup(cls):
		cls.node_list.clear()
		
	#-------------------------------------------------------------
	# 
	#------------------------------------------------------------
		
	@classmethod
	def shutdown(cls):
		for lg in cls.node_list:
			if lg.is_active:
				lg.close_writer()
	
			
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
		
def main(msgr):
	
	#-------------------------------------------------------------
	# 
	#------------------------------------------------------------
	
	curdir = pathlib.Path().cwd()
	
	file_list = build_file_list(curdir, '*.py')
	
	msgr.write_msg(f'{LF} {len(file_list)} [.py] files in {curdir} dir tree. {LF}')
	
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
	
	fileprefix = str(pathlib.Path(__file__).stem)
	
	Message_Writer.setup()
	
	msgr = Message_Writer(name='root',prefix=fileprefix)
	
	msgr.write_msg(f'{LF}program {__file__} started. {LF}')
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	main(msgr)
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
	
	msgr.write_msg(LF)
	msgr.write_msg(f'{LF}program {__file__} completed. {LF}')
	
	msgr.close_writer()
	
	Message_Writer.shutdown()
	
	#-------------------------------------------------------------
	# 
	#-------------------------------------------------------------
