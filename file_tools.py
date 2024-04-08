import os
import glob 

class FileTools :
    last_metadata_path = None
    enabled = False

    def get_most_recent_file(self, path, extension = '*.mp4') :
        try :
            # list_of_files = glob.glob(extension)
            list_of_files = glob.glob(os.path.join(path, extension))
            list_of_files.sort(key=os.path.getctime, reverse=True)
            
            output_list = []
            for file in list_of_files :
                output_list.append(os.path.basename(file))
        except :
            return None

        return output_list
    
    def metadata_check(self, file):
        self.last_metadata_path = file
        if os.path.exists(file):
            return True
        else :
            return False
    
    def delete_metadata(self, file):
        if os.path.exists(file):
            os.remove(self.last_metadata_path)

    def check_validity(self, video_list, metadata_list):
        # Extract file names from each list
        video_list = set([filename.split('.')[0] for filename in video_list])
        metadata_list = [filename.split('.')[0] for filename in metadata_list]

        # Find the common file names between the two lists
        # common_filenames = list(set(metadata_list).intersection(video_list))
        ready_list  = [file for file in metadata_list if file in video_list]
        
        return ready_list

    def get_files_to_process(self, path, extension = ".mp4") :
        try :
            list_of_files = glob.glob(os.path.join(path, "*"+extension))
            list_of_files.sort(key=os.path.getmtime, reverse=False)

            list_of_metadata = glob.glob(os.path.join(path, "*.botabot"))
            list_of_metadata.sort(key=os.path.getmtime, reverse=False)
            
            ready_list = self.check_validity(list_of_files,list_of_metadata)
            
            output_list = []
            for file in ready_list :
                output_list.append(os.path.basename(file+extension))

        except :
            return None

        return output_list

filetools = FileTools()