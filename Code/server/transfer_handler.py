 
import os 

import shutil 

from common.constants import CHUNK_SIZE, MIN_FREE_SPACE_BUFFER, SERVER_ERROR_OFFSET 

from common.protocol import receive_upload_header, send_offset 

from common.utils import sanitize_subfolder, unique_file_path 

 

class TransferHandler: 

    def __init__(self, upload_dir): 

        self.upload_dir = os.path.abspath(upload_dir) 

 

    def prepare_destination(self, sock): 

        header = receive_upload_header(sock) 