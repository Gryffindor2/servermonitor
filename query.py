import paramiko
from apscheduler.schedulers.blocking import BlockingScheduler

server_list = {}

def clock_events():
    to_be_deleted_ip_list = []
    for key in server_list:
        value = server_list[key]
        if value["life"] > 0:
            value["life"] -= 1
        else:
            value["server"].disconnect()
            to_be_deleted_ip_list.append(key)
    for ip in to_be_deleted_ip_list:
        del server_list[ip]
    
            
def start_moniting():
    sched = BlockingScheduler()
    sched.add_job(clock_events, 'interval', seconds=20)
    sched.start()

class ssh_server:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        self.connect_error = False
    

    def alive(self):
        if self.ip in server_list:
            server_list[self.ip]["life"] = 5
        else:
            temp = {}
            temp['server'] = self
            temp["life"] = 5
            server_list[self.ip] = temp

    def connect(self):
        if self.ip in server_list:
            self.alive()
            print('already connected to ' + self.ip, end = ' ')
        else:
            print('connect to ' + self.ip, end = ' ')
            try:
                self.server = paramiko.SSHClient()
                self.server.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.server.connect(self.ip, username=self.username, password=self.password, timeout=10)
                self.connect_error = False
                self.alive()
                print('\033[92mOK\033[0m')
            except Exception as ex:
                self.connect_error = True
                print(ex)
                print("\033[91mfailed\033[0m")

    def status(self):
        return not self.connect_error
    
    def check_program(self, program_name):
        if self.connect_error:
            return 'connection failed'
        output = self.execute("which " + program_name)
        if output:
            return True
        else:
            return False

    def check_file(self, path, filename):
        if self.connect_error:
            return 'connection failed'
        output = self.execute("find " + path + filename + "-name " + filename)
        if output:
            return True
        else:
            return False

    def execute(self, command):
        if self.connect_error:
            return 'connection failed'
        stdin, stdout, stderr = self.server.exec_command(command)
        output = stdout.read().decode().strip()
        return output
    
    def check_cpu(self):
        if self.connect_error:
            return 'connection failed', 'connection failed'
        cpu_model = (self.execute("lscpu | grep 'Model name'").split(':')[-1]).strip()
        cpu_cores = self.execute("lscpu | grep ^CPU\(s\)").split()[-1]
        return cpu_model, cpu_cores

    def check_mem(self):
        if self.connect_error:
            return 'connection failed'
        mem_info = (self.execute("free -h | grep Mem").split())[1]
        mem_size = float(mem_info[:-1])
        return mem_size

    def check_disk(self):
        if self.connect_error:
            return 'connection failed'
        disk_info = self.execute("lsblk | grep -E ^sd[a-z]").split('\n')
        size_list = []
        for rec in disk_info:
            size_list.append(rec.split()[-3])
        total_size = 0 #G
        for size in size_list:
            unit = size[-1]
            size = float(size[:-1])
            if unit == 'G':
                total_size += size
            elif unit == 'T':
                total_size += size * 1024
            elif unit == 'M':
                total_size += size / 1024
        return round(total_size, 2)

    def check_gpu(self):
        if self.connect_error:
            return 'connection failed'
        gpu_info = self.execute("nvidia-smi -L").split('\n')
        
        gpu_list = []
        for gpu in gpu_info:
            start_index = gpu.find(":") + 2
            end_index = gpu.find("(") - 1
            
            gpu_model = gpu[start_index:end_index]
            gpu_list.append(gpu_model)
        return gpu_list
    
    def check_gpu_usage(self):
        if self.connect_error:
            return 'connection failed'
        gpu_info_useage = self.execute("nvidia-smi | grep %").split('\n')
        usage_list = []
        for usage in gpu_info_useage:
            usage_list.append(int(usage[1:].split('%')[0]))
        print(usage_list)
        return usage_list


    def disconnect(self):
        if self.connect_error == False:
            self.server.close()
            print('disconnect from ' + self.ip)

    def __del__(self):
        self.disconnect()
    
    @staticmethod
    def new(ip, username, password):
        if ip in server_list:
            return server_list[ip]["server"]
        else:
            return ssh_server(ip, username, password)
