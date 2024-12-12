import time

class Benchmark():
    def __init__(self, bench_name = None):
        if bench_name is not None: 
            self.bench_name = bench_name
        else:
            self.bench_name = '---------------'
        self.sequence = {}
        self.current_operation = None
        self.currentoperation_start_time = None

    def start(self, operation_name):
        if self.current_operation is not None:
            self.stop()            
        self.current_operation = operation_name
        self.currentoperation_start_time = time.time()

    
    def stop(self):
        duration = time.time() - self.currentoperation_start_time
        if self.current_operation in self.sequence:
            self.sequence[self.current_operation].append(duration)
        else:
            self.sequence[self.current_operation] = [duration]
        
        self.current_operation = None
        self.currentoperation_start_time = None

    def join(self, other_benchmark):
        for k, v in other_benchmark.sequence.items():
            if k in self.sequence:
                self.sequence[k].extend(v)
            else:
                self.sequence[k] = v
        

    def get_avarage_list(self):
        avarage_sequence = {}
        for k, v in self.sequence.items():
            avarage_sequence[k] = sum(v) / len(v)
        return avarage_sequence
    
    def get_top_10_longest_avarage(self):
        avarage_sequence = self.get_avarage_list()
        if len(avarage_sequence) < 10:
            return sorted(avarage_sequence.items(), key=lambda x: x[1], reverse=True)
        return sorted(avarage_sequence.items(), key=lambda x: x[1], reverse=True)[:10]
    
    def get_report(self, sort_descending = True):
        report_lines = []
        entries = self.get_avarage_list().items()
        if sort_descending:
            entries = sorted(entries, key=lambda x: x[1], reverse=True)
        
        report_lines.append(f'Benchmark: {self.bench_name}')
        for key, value in entries:
            report_lines.append(f'{value:.5f} : {key} ')
        
        report = '\n'.join(report_lines)
        report += f'\nEND {self.bench_name} END'
        return report
    
    def print_report(self, sort_descending = True):
        print(self.get_report(sort_descending))


