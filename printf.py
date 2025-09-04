# slow print for C I N E M A
from sys import stdout
#from termcolor import color
from time import sleep
def printb(text, pause = 0.03):
  for i in text:
    # coloring = color(i,color)
    stdout.write(i)
    stdout.flush()
    sleep(pause)
