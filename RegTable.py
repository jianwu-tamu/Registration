

class RegTable:
    def __init__(self, watch_number):
        self.watch_number = watch_number
        self.regTable = {}
        self.pair_status = {}
        self.unpair_watch = " "

    def create_table(self, presenter_name, watch_name):
        assert(len(self.regTable) < self.watch_number)
        if((not self.pair_status.get(watch_name)) or (self.pair_status.get(watch_name) == 0)):
            self.regTable[watch_name] = presenter_name
            self.pair_status[watch_name] = 1
            print self.regTable
            print self.pair_status

    def update_table1(self, presenter_name):
        assert(len(self.regTable) == self.watch_number)
        assert(self.regTable[self.unpair_watch] == " ")
        self.regTable[self.unpair_watch] = presenter_name
        print self.regTable

    def unpair(self, watch_name):
        self.regTable[watch_name] = " "
        self.unpair_watch = watch_name
        print self.regTable