import paramiko

class client:
    def __init__(self, ip, username, password):
        self.ip = ip
        self.username = username
        self.password = password
        print('connect to ' + ip, end = ' ')
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.client.connect(self.ip, username=self.username, password=self.password, timeout=5)
            self.connect_error = False
            print('\033[92mOK\033[0m')
        except:
            self.connect_error = True
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
        stdin, stdout, stderr = self.client.exec_command(command)
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
    
    def __del__(self):
        if self.connect_error == False:
            self.client.close()