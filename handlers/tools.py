from base import HandlerBase

class OneTimeUse(HandlerBase):
    def get(self):
        # code I want to execute once
        self.write("Success!")