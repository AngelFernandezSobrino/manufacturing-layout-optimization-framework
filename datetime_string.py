import datetime

now = datetime.datetime.now()

# From the date_time variable, you can extract the date in various
# custom formats with .strftime(), for example:
now_string = now.strftime("%Y_%m_%d_%H_%M_%S")
