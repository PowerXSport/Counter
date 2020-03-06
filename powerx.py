import kivy
import RPi.GPIO as GPIO
import time

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.properties import StringProperty
from kivy.clock import Clock

plusButtonPinNum = 13
minusButtonPinNum = 15
buttonPinNum = 16
buzzerPinNum = 12

totalSeconds = 60
maxReps = 0

def gpio_init():
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(buttonPinNum, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(plusButtonPinNum, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(minusButtonPinNum, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
	GPIO.setup(buzzerPinNum, GPIO.OUT)


def formatTime(time):
	minutes = time / 60
	seconds = time % 60
	return "{0}:{1:02d}".format(minutes, seconds)

class PowerXCounter(GridLayout):
	num = 0
	totalTimeSeconds = totalSeconds
	previousInput = 0

	#PROPERTIES
	timeRemaining = StringProperty(formatTime(totalTimeSeconds))
	counter = StringProperty("0")
	totalTons = StringProperty("0")
	weight = StringProperty("65")

	def __init__(self, **kwargs):
		super(PowerXCounter, self).__init__(**kwargs)
		self.reset()
		Clock.schedule_interval(self.checkInput, 0.15)

	def reset(self):
		#GPIO / CLOCK RESET
		Clock.unschedule(self.timer, 1)
		Clock.schedule_once(self.buzzeroff)

		#RESETS VARS	
		self.num = 0
		self.totalTimeSeconds = totalSeconds
		self.previousInput = GPIO.input(buttonPinNum)
		self.countdowninprogress = False
		self.countdownnum = 3
		self.buzzerlength = 1
		self.timerRunning = False

		#RESET LABELS
		self.counter = "0"
		self.timeRemaining = formatTime(totalSeconds)
		self.weight = "65"
		self.totalTons = "0"

	def checkInput(self, dt):
		#COUNTER BUTTON PRESS
		input = GPIO.input(buttonPinNum)
		if input != self.previousInput:
			self.previousInput = input
	            	if not self.countdowninprogress:
				self.click()
		# +/- BUTTON PRESS
		if not self.timerRunning and not self.countdowninprogress and self.num == 0:
			plus = GPIO.input(plusButtonPinNum)
			minus = GPIO.input(minusButtonPinNum)
			w = int(self.weight)
			if plus and w < 1000:
				w += 5
			if minus and w > 65:
				w -= 5
			self.weight = str(w)

	def countdown(self, dt):
		if self.countdownnum > 0:
			self.countdowninprogress = True
			self.totalTons = "{0}".format(self.countdownnum)
			self.countdownnum -= 1
		else:
			self.totalTons = "GO!"
			self.countdowninprogress = False
			Clock.unschedule(self.countdown)
			Clock.schedule_once(self.buzzer)
			Clock.schedule_once(self.setnum, 0.5)
			Clock.schedule_interval(self.timer, 1)

	def setnum(self, dt):
		self.totalTons = "0"

        def settons(self):
                self.totalTons = str(self.num * int(self.weight))

	def buzzeroff(self, dt):
		GPIO.output(buzzerPinNum, False)

	def buzzer(self, dt):
		GPIO.output(buzzerPinNum, True)			
		Clock.schedule_once(self.buzzeroff, self.buzzerlength)

	def click(self):
		if self.countdowninprogress:
			return

		if self.totalTimeSeconds == 0:
			self.reset()
		else:
			if self.num == 0:
				Clock.schedule_interval(self.countdown, 1)
			elif self.num < maxReps or maxReps == 0:
				self.counter = str(self.num)
                                self.settons()
			elif self.num == maxReps:
				self.counter = str(maxReps)
                                self.settons()
				Clock.unschedule(self.timer, 1)
			else:
				self.reset()
				return

			self.num += 1

	def timer(self, dt):
		self.totalTimeSeconds -= 1
		self.timerRunning = True
		self.timeRemaining = formatTime(self.totalTimeSeconds)
		if self.totalTimeSeconds == 0:
			Clock.unschedule(self.timer)
			self.buzzerlength = 3
			self.timerRunning = False
			Clock.schedule_once(self.buzzer)

class PowerXApp(App):
	def build(self):
		gpio_init()
		return PowerXCounter()
	
if __name__ == "__main__":
	PowerXApp().run()

GPIO.output(buzzerPinNum, False)
GPIO.cleanup()
